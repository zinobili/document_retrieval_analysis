from flask import Flask, render_template, session, request
from flask import Flask, jsonify
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit
import time
from datetime import datetime
import os

## cognitive search
from python_module import cog_search

## LLM information extraction
from python_module import info_extraction

# file_path='./static/uploads/2022042101281.pdf'
# docsearch=cog_search.build_vector_DB(file_path)
# docsearch = cog_search.quick_load_a_docsearch(file_path) # skip the process
# excel_path='./static/esg_question/question_base_test.xlsx'
# QA = info_extraction.llm_question_answering(docsearch, 
#                                             question_excel_path=excel_path,
#                                             result_path=f'./static/working_file/result/result_{current()}.csv'
#                                             )



## reading csv result
import pandas as pd

app = Flask(__name__)
app.secret_key = "your_secret_key"
socketio = SocketIO(app, manage_session=False)

app.config['UPLOAD_FOLDER']='./static/uploads/'
# excel_path='./static/esg_question/question_base_test.xlsx'
excel_path='./static/esg_question/question_base.xlsx'

@app.route('/')
def index():
    update_progress("nothing started")
    return render_template('landing.html')

@app.route('/comparison')
def comparison():
    update_progress("nothing started")
    return render_template('landing.html',compare=True)

@app.route('/result')
def result():
    try:
        file_path=session.get('result_path')
    except:
        file_path='./static/working_file/mockup.csv'
    df=pd.read_csv(file_path)
    result=csv_to_list_of_dicts(file_path)
    print(result)
    multi=session['multi']
    if multi==1:
        return render_template('landing.html',result=result,multi=multi,compare=True)
    else:
        return render_template('landing.html',result=result,multi=multi)


@app.route("/analyze", methods=["POST"])
def start_process():
    # Start the long-running process here
    # This may involve running a separate function or spawning a new thread

    
    ## file handling

    # Check if a file was uploaded
    if 'file' not in request.files:
        print('no file uploaded')
        return jsonify({'error': 'No file uploaded'})
    file = request.files['file']
    filename = secure_filename(file.filename)
    print(filename)
    file_path=os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)


    ## vector database
    update_progress("building vector database")

    docsearch = cog_search.build_vector_DB(file_path) # run the process
    # docsearch = cog_search.quick_load_a_docsearch(file_path) # skip the process
    

    ## question answering
    update_progress("information retrieval")
    result_path=f'./static/working_file/result/result_{current()}.csv'
    QA = info_extraction.llm_question_answering(docsearch, 
                                                question_excel_path=excel_path,
                                                result_path = result_path,
                                                )
    session['result_path']=result_path
    session['multi']=0

    # Notify the frontend that the process is complete
    # socketio.emit("process_complete", {"message": "Processing task finished"})

    return jsonify({"status": "Process completed"})

@app.route("/analyze_multi", methods=["POST"])
def start_process_multi():
    # Start the long-running process here
    # This may involve running a separate function or spawning a new thread

    
    ## file handling

    # Check if a file was uploaded
    if 'file' not in request.files:
        print('file1 not uploaded')
        return jsonify({'error': 'file1 not uploaded'})
    file = request.files['file']
    filename = secure_filename(file.filename)
    print(filename)
    file_path=os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Check if 2nd file was uploaded
    if 'file2' not in request.files:
        print('file2 not uploaded')
        return jsonify({'error': 'file2 not uploaded'})
    file2 = request.files['file2']
    filename2 = secure_filename(file2.filename)
    print(filename2)
    file_path2=os.path.join(app.config['UPLOAD_FOLDER'], filename2)
    file2.save(file_path2)


    ## vector database
    update_progress("Company A - building vector database")
    docsearch_A = cog_search.build_vector_DB(file_path) # run the process
    # docsearch_A = cog_search.quick_load_a_docsearch(file_path) # skip the process

    update_progress("Company B - building vector database")
    docsearch_B = cog_search.build_vector_DB(file_path2) # run the process
    # docsearch_B = cog_search.quick_load_a_docsearch(file_path2) # skip the process
    

    ## question answering
    result_path=f'./static/working_file/result/result_{current()}.csv'
    result_path_A=result_path.replace('.csv','_A.csv')
    result_path_B=result_path.replace('.csv','_B.csv')
    
    update_progress("Company A - information retrieval")
    QA = info_extraction.llm_question_answering(docsearch_A, 
                                                question_excel_path=excel_path,
                                                result_path = result_path_A,
                                                )
    
    update_progress("Company B - information retrieval")
    QA = info_extraction.llm_question_answering(docsearch_B, 
                                                question_excel_path=excel_path,
                                                result_path = result_path_B,
                                                )
    
    result_df = combine_result_A_B(result_path_A=result_path_A,
                                   result_path_B=result_path_B,
                                   output_path=result_path)


    session['result_path']=result_path
    session['multi']=1

    # Notify the frontend that the process is complete
    # socketio.emit("process_complete", {"message": "Processing task finished"})

    return jsonify({"status": "Process completed"})

@app.route("/progress")
def get_progress():
    # Return the progress status to the client
    # You can calculate the progress based on your specific logic

    # For demonstration purposes, let's return the current progress stored in the session
    progress = read_progress()
    print(progress)
    if progress[-3:]!='...':
        progress+='.'
    else:
        progress=progress[:-3]
    update_progress(progress)

    return jsonify({"progress": progress})


import csv

def csv_to_list_of_dicts(file_path):
    data = []
    
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    
    return data

def update_progress(status):
    with open('./static/working_file/progress.txt', 'w') as file:
            file.write(status)  # Write the session data to the text file
    return

def read_progress():
    with open('./static/working_file/progress.txt', 'r') as file:
        status = file.read()  # Read the session data from the text file
    return status

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def current():
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    return timestamp

def combine_result_A_B(result_path_A,result_path_B,output_path):
    dfA = pd.read_csv(result_path_A)
    dfB = pd.read_csv(result_path_B)
    dfA.columns = ['Question','Answer_A','Source_A','Reason_A']
    dfB.columns = ['Question_B','Answer_B','Source_B','Reason_B']
    df_combined=pd.concat([dfA,dfB],axis=1)
    df_combined.to_csv(output_path,index=0)
    return df_combined


# if __name__ == '__main__':
if __name__ == "__main__":
    socketio.run(app)