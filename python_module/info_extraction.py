'''
pip install openpyxl
pip install openai
'''

import os 
import openai
import pandas as pd


with open('./config/key.txt', 'r') as file:
        openAIKey = file.read()
os.environ["OPENAI_API_KEY"] = openAIKey

def llm_question_answering(docsearch, question_excel_path, result_path):
    print(f"start QA according to path: {question_excel_path}")
    df = pd.read_excel(question_excel_path)
    df['query_ask']=df.query_search.map(lambda x: x.split('\n')[0])

    result_list=[]

    for index, row in df.iterrows():
        query_search=row.query_search
        query_ask=row.query_ask
        require=row.require
        print(f"q_search:{query_search}")
        print(f"q_ask:{query_ask}")
        print(f"require:{require}")
        rst = knowledge_extraction(query_search=query_search,query_ask=query_ask,require_format=require,docsearch=docsearch,
                        need_reason=1,
                        rough_prompt=0
                        )
        to_append={
            'Question': query_ask,
            'Answer': rst['answer'],
            'Source': rst['page_number'],
            'Reason': rst['reason'],
        }
        print(to_append)
        result_list.append(to_append)
        print('====')


    ## save to csv
    df = pd.DataFrame(result_list)
    df.to_csv(result_path,index=0)


    return True


def build_instruction(require,need_reason=0):
    if require=='numeric':
        delivery={'NA':'0', 'answer': 'a quantitative figure in string only'}
    else:
        delivery={'NA': 'FALSE', 'answer': 'TRUE or FALSE in string only'}

    if need_reason==1:
        reason=''' , 'reason for the answer' '''
    else:
        reason=''

    instruction= """
    You are a helpful assistant and document reader. 
    You will read through the context content and answer the question based on it. 
    Do not try to make up anyhing. If answer is not provided, respond: ('__NA__' __reason__)
    Format of response should be the following: ('__answer__' __reason__)
    """

    instruction=instruction.replace('__NA__',delivery['NA']).replace('__answer__',delivery['answer'])
    instruction=instruction.replace('__reason__',reason)

    return instruction

## warp-up function
import json

def knowledge_extraction(query_search,query_ask,require_format,docsearch,need_reason,rough_prompt=0):
    """
    input:
        search_query:   the query raise for searching
        question_query: the query for question answer in extracted context
        require_format: whether u want 'numeric' or 'bool'
        docsearch:      a langchain.vectorstores.faiss.FAISS class for chroma equivalent class
        need_reason:    whether u want a reason fromt the llm
        rough_prompt:   whether to use a basic prompt
    output a dictionary where::
        
        
    """
    
    ## find content
    docs = docsearch.similarity_search(query_search)
    page_numbers = [str(x.metadata['page']) for x in docs][:3]
    page_numbers_str = ', '.join(list(set(page_numbers)))
    
    k=3
    content = '\n\n'.join([x.page_content for x in docs[:k]])
    
    ## build prompt
    prompt="""Based on the content below, answer the question as written in query
    content:{},
    query:{}
    """.format(content,query_ask)
    
    ## instruction from system
    instruction=build_instruction(require=require_format,need_reason=need_reason)
    
    ## message
    messages=[
                {
                  "role": "system",
                  "content":instruction
                },
                {
                  "role": "user",
                  "content": f"{prompt}"
                }
    ]
    
    ## change to rough prompt
    if rough_prompt==1:
        require_string="Answer a numerical figure." if require_format=='numeric' else "Answer True or False."
        messages=[
                {
                  "role": "user",
                  "content": f"{prompt} \n Answer {require_string} "
                }
        ]
        
#     print(messages)
    
    
    ## API calling
    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.01,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    
    ## wrap up result
#     print(completion)
    rst=(completion.choices[0].message.content)
#     print(rst)
#     print(type(rst))
    try:
        rst={'answer':rst.split(',')[0].replace('(','').replace(')','').replace('\'','').replace('\"',''),
             'reason':','.join(rst.split(',')[1:])}
    except:
        rst={'answer':rst,'reason':'NA'}
    if not isinstance(rst,dict):
        rst={'answer':rst}        
    rst['usage']=completion.usage.total_tokens
    rst['response']=completion
    rst['instruction']=instruction
    rst['source']=content
    rst['page_number']=page_numbers_str
    
    return rst