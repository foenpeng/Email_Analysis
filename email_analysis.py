
# coding: utf-8

# In[103]:

# This program runs locally to extract email sending and receiving information from an email box, then 
# count the frequency of email communication between each pair of sender and receiver and deposit them into a sqlite database.


# In[104]:

import sqlite3
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt



# In[105]:

def open_db(cur):
    # this function opens a table to deposit the email information.
    # cur is the cursor
    
    cur.execute('''DROP TABLE IF EXISTS Connections ''')
    cur.execute('''CREATE TABLE Connections (from_address TEXT, from_domain TEXT, from_note TEXT, 
                                            to_address TEXT, to_domain TEXT, to_note TEXT,
                                            count INTEGER)''')


# In[106]:

def find_email(line):
    # this function looks for the email addresses in lines.
    # line is a string
    
    is_email = False
    address, domain, note = None, None, None
    pieces = line.split()
    
    for piece in pieces:
        position = piece.find("@")
        if position != -1 : 
            is_email = True
            domain = piece[position + 1:].split('>')[0] 
            address = piece[: position].strip('<') + "@" + domain
            domain = domain.strip('", ''()')
            address = address.strip('", ''()')                     
            note = ' '.join(pieces[1:-1])
            break
            
    return is_email, address, domain, note


# In[107]:

def edit_db(from_address, from_domain, from_note, to_address, to_domain, to_note):
    # this function insert the email sender and receiver information into database and count the frequency of each pair of communication
    # all the inputs are string
    
    cur.execute('SELECT count FROM Connections WHERE from_address = ? AND to_address = ?',( from_address, to_address,))
    record = cur.fetchone()
    
    if record is None:
        cur.execute('''INSERT INTO Connections (from_address, from_domain, from_note,
                                        to_address, to_domain, to_note,
                                        count) 
                                 VALUES(?,?,?,?,?,?, 1)''', (from_address, from_domain, from_note,to_address, to_domain, to_note))
    else:
        cur.execute('''UPDATE Connections SET count = count +1 WHERE from_address = ? AND to_address = ?''',(from_address, to_address))
    
    conn.commit()


# In[108]:

def parse_file(file):
    # this function parse the file to find email address and domain information
    # file is a file handler
    
    mail_nums = 0
    for line in file:

        # disregard other lines
        if not line.startswith('From: '): continue

        # look for email address
        from_email = find_email(line)

        if from_email[0]:
            from_address = from_email[1]
            from_domain = from_email[2]
            from_note = from_email[3]

            # if find a line containing sender info, look for receiver information in next five lines
            for i in range(5):
                new_line = next(file)
                if not new_line.startswith('To: '): continue
                to_email = find_email(new_line)
                if to_email[0]:
                    to_address = to_email[1]
                    to_domain = to_email[2]
                    to_note = to_email[3]
                    break


            # disregard syntax errors when inserting into database
            try:
                edit_db(from_address, from_domain, from_note,to_address, to_domain, to_note )
                
            except Exception:
                print(from_address)
                pass

            #mail_nums  += 1
            #if mail_nums > 5000:
                #break


# In[109]:

def extract_df(my_address):
   
    placeholders= ', '.join('"'+item+'"' for item in my_address)
    
    # extracting sender information
    sqlitestr_from = '''SELECT from_address, to_address, count FROM Connections 
                   WHERE from_address IN ({0})
                   ORDER BY count DESC'''.format(placeholders)
    df_from = pd.read_sql_query(sqlitestr_from, conn)

    # extracting receiver information
    sqlitestr_to = '''SELECT from_address, to_address, count FROM Connections 
                   WHERE to_address IN ({0})
                   ORDER BY count DESC'''.format(placeholders)
    df_to = pd.read_sql_query(sqlitestr_to, conn)    
    
    return df_from, df_to


# In[110]:

def find_mutual(df_from, df_to):
    # this function looks for mutual contacts in the two data frames
    
    # swap the sender and receiver in one of the data frames
    col_ls = list(df_from)
    col_ls[0], col_ls[1] = col_ls[1], col_ls[0]
    df_swap_from = df_from.copy()
    df_swap_from.columns = col_ls
    
    df_merge = df_to.merge(df_swap_from, how ="inner", on=["from_address", "to_address"])
    
    return df_merge


# In[111]:

def combine_my_address(df, my_address, myself):
    # this function substitute all my addresses with my name, because I have multiple addresses

    df.ix[:,0:2] = df.ix[:,0:2].replace(my_address,myself)

    # combine the information if a same sender sent emails to my different addresses
    df_combined = df.groupby(['from_address','to_address'])['count'].sum().reset_index()
    
    return df_combined


# In[112]:

def clean_merge(df_merge, myself):
    df_merge = df_merge[['from_address','count_x','count_y']]
    df_merge.columns = ["contacts", "receving counts", "sending counts"]

    # I used a customized equation to evaluate the importace of contacting people
    df_merge['score'] = np.around(np.sqrt(df_merge["receving counts"] * df_merge["sending counts"]),decimals=2)
    df_merge = df_merge.sort_values(by=["score"],ascending=False)
    df_merge = df_merge[df_merge.contacts != myself]
    
    return df_merge


# In[113]:

def find_names(df_merge):
    # this function look for the corresponding names of the contacts' email address

    names = []
    for element in df_merge.contacts:
        cur.execute("SELECT from_note FROM Connections WHERE from_address = ?",(element,))

        name = cur.fetchone()[0].encode('ascii','ignore')
        name = name.decode("utf-8") 
        name.strip('"')

        names.append(name)

    df_merge['Names'] = names
    
    return df_merge


# In[114]:

def draw_network(df_merge, myself, node_number = 10):
   # this function use the df_merge data frame draw a network graph.
   # node_number is an integer, defined as how many nodes connecting to the center are expected in the graph
   
   df_graph = df_merge.head(node_number)

   G = nx.Graph()

   edges = []
   for index,row in df_graph.iterrows():
       G.add_edge(row[-1], myself,length=row[-2])
       edges.append((row[-1], myself))

   edge_labels = dict(zip(edges, df_graph.score))

   node_score = df_graph.set_index('Names')['score'].to_dict()
   size_values = [node_score.get(node, 20)*20 for node in G.nodes()]
   
   #nx.draw_networkx(G)
   pos = nx.spring_layout(G)
   nx.draw_networkx_nodes(G,pos,node_size=size_values,alpha=0.3, node_color='blue')
   nx.draw_networkx_edges(G,pos,width=1,alpha=0.3,edge_color='blue')
   nx.draw_networkx_labels(G,pos,font_size=8,font_family='sans-serif')
   nx.draw_networkx_edge_labels(G, pos, edge_labels,label_pos=0.5,font_size=8)
   
   plt.axis('off')
   plt.show()


# In[115]:

if __name__ == "__main__":
    
    user_name = input("What's your name? \n")
    my_address = list(input('''What's all your email addresses? Please put a space in between each address. 
    For example, I have forwarded all my uw emails to my gmail account. So I would input as:
    peng.foen@gmail.com foenpeng@uw.edu foenpeng@u.washington.edu \n''').split())
    
    # construct a list with all my possible email addresses   
    my_address.extend(list(map(lambda x:x.upper(),my_address)))
    
    db = user_name + "_emaildb.sqlite"
    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        open_db(cur)
        
        
        with open("my_emails.mbox") as file:
            parse_file(file)
        
        # extract sender and receiver email address and deposit to database
        df_from, df_to = extract_df(my_address)
        
        # combine my addresses in the data frames. Please change the following addresses to your own email addresses
        # and change 'Foen' to Your name with a quote sign
        if len(my_address) > 1:
            df_from = combine_my_address(df_from, my_address, user_name)        
            df_to = combine_my_address(df_to, my_address, user_name)
        
        # find the mutual contacts in the two data frames
        df_merge = find_mutual(df_from, df_to)
        
        # clean and sort the merged dataframe
        df_merge = clean_merge(df_merge, user_name)
        
        # look for contacts' names and store them as a column in dataframe
        df_merge = find_names(df_merge)
        
    # visualize the network graph with package networkx
    node_numbers = int(input('''Analysis completed! How many nodes do you want to see in your email network? 
    A value between 5-20 would be ideal for visualization
    The program will be closed after you close the plot window. 
    Enter the value: \n'''))
    
    print(df_merge.head(node_numbers))
    draw_network(df_merge, user_name, node_numbers) 
    

