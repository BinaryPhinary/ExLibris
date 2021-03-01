
############################################################################################################
##
## The purpose of this code is to take an Ansible Fact which lists Cron Jobs for all servers in an inventory,
## And turn it into a Valid JSON.  There are a few steps to do this,
## After which we pull the data from the JSON and output it to a Text File which can be opened and used as a CSV
##
## Authors:  Lior Cohen, Eric Taylor
## Date: Jan 28th 2021
##
import json
import csv
import os
import glob
import re
import ipaddress
import copy
import sys

#########################################
# Hardcoded file locations
# outputfile is where we store the edited broken JSON after some manipulations.  Further work could be done
# to remove the need for this file by writing it back to a list instead.  Another version can solve this issue
# test_json is a path to a 'good' JSON file for testing the parsing and writing to an output file
# txt_out is our final output
# This could be made more dynamic with a small amount of work by creating a random extension
# On the file name.  This could be a future improvement for another version
test_json = 'C:/Users/Eric/OneDrive/Documents/Scripts/ansible_cron/archive/new/test_json.json'
txt_out = 'C:/Users/Eric/OneDrive/Documents/Scripts/ansible_cron/archive/new/comma_text.txt'
outputfile = 'C:/Users/Eric/OneDrive/Documents/Scripts/ansible_cron/archive/new/dump2.json'

json_fn_path=input("Please enter the path where the JSON File can be located: \n")

json_find = ""
loc_json= ""
loc_json_split = ""

for root, dirs, files in os.walk(json_fn_path):
    for file in files:
         if file.endswith('json'):
            foundit5 = True
            loc_json=(os.path.join(root, file))
    if foundit5 == True: break     

else:
    loc_json="" #Setting a value to loc in the event that no JSON files are found - otherwise no value would be set in loc which would break the approach to create loc_split

if loc_json != "": # If we find that loc has a value then we take the next step - splitting the loc destimation to get the path that we can use later in the code
   loc_json_split=os.path.dirname(loc_json)
   #print(loc_json_split)
   print("JSON has been located, moving on")

else:
    print("No JSON found - exiting")
    sys.exit(5)

def remove_success(filein, fileout): #This function removes the | SUCCESS => from the broken JSON at the top of the file
    delete_list = ['| SUCCESS =>']
    lst = []
    with open(filein, 'r+') as fin, open(fileout, 'w') as fout:
        for line in fin:
            for word in delete_list:
                if word in line:
                    line = line.replace(word,"")
            lst.append(line)
        for line in lst:
            fout.write(line)

def remove_warnings(filein, fileout):
    with open(filein, 'r+') as infile, open(fileout, 'w') as fout:
            aline = infile.read()
            print(aline)
            #temp_replace = re.sub(r"(*\[)WARNING(\])(.*)\s(.*)\s(.*)\s(.*)\s(.)", "", aline)
            temp_replace = re.sub(r"(?=\[).+?(?<=\])(.+\s\S.*.+\s*\S*.+\s*\S*.*.+\s*).*(\s*).*", "", aline)
            temp_replace = fout.write(temp_replace)

def remove_uncreachable(filein, fileout):
        with open(filein, 'r+') as infile, open(fileout, 'w') as fout:
            aline = infile.read()
            temp_replace = re.sub(r'(.* \| UNREACHABLE!)(.*\s*.*\s*.*\s*.*\s.*)', "", aline)
            temp_replace = fout.write(temp_replace)

def find_hostname(filein, fileout):
    newhname_lst = []
    with open(filein, 'r+') as infile, open(fileout, 'w') as fout:
        for aline in infile:
                aline = infile.read().splitlines()
                for i in aline:
                    temp_hname = re.findall(r"^.*dc\d*", i)
                    temp_hname_str = ''.join(temp_hname)
                    temp_hname_q = '"' + temp_hname_str + '"' + ':'
                    aline = re.sub(
                        r"^.*dc\d*",
                        temp_hname_q,
                        i 
                        )
                    newhname_lst.append(aline)
        for line in newhname_lst:
            fout.write(line + '\n')

#C:\Users\Eric\OneDrive\Documents\Scripts\Comment Cron

def top_bottom(eatfile): #This adds a { to the top of the file as we want to make a valid JSON
    with open(eatfile, 'r+') as infile:
        content = infile.read()
        infile.seek(0,0)
        infile.write("\n")
        infile.write(str('{') + "\n")
        infile.write(content + "\n" + "}")    

def quote_ip_fix(infile, outfile): # This places quotes around the IP address and adds a colon - again - to make it a Valid JSON
    newip_lst = []
    with open(infile, 'r') as subin, open(outfile, 'w') as subout:
        for aline in subin:
            aline = subin.read().splitlines()
            for i in aline:
                temp_ip = re.findall(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", i)
                temp_ip_str = ''.join(temp_ip)
                temp_ip_q = '"' + temp_ip_str + '"' + ':' 
                aline = re.sub(
                r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
                    temp_ip_q,
                    i 
                    )
                newip_lst.append(aline)
        for line in newip_lst:
            subout.write(line + '\n')

#top_bottom(loc_json)

#quote_ip_fix(loc_json, outputfile)

def the_brackets(find1, find2, infile, outfile):  #This function is designed to find and replace issues with } brackets to make the JSON structure work
    count1 = 0 #this is to count the number of times we need insert a }, - wich should be every 5th instance of }
    count2 = 0 # We will insert 1 too many },'s - which will always be the second last } in the JSON.  This will be replaced with a }
    to_find = [find1] #This is just a ref back to the input - putting it in list form
    tmp_list = [] #To temporarily hold a list of our edits we've made so we can write them back to file
    brckt_list = [] #This is to store the total number of times we find a } within the list after we add in commas to existing brackets
    total_brackt = [] #Almost not needed - its to store the value of the len of the brack list minus 1.  This allows us to count to get the right } to change
    new_tmp = [] # this is a list to store all of the values after we amend the errant }, to a }.  Storing to the existing list was problematic
    with open(infile, 'r') as readfile, open(outfile, 'w') as writefile:
        file_b = readfile.read()
        for i in file_b:
            for item in to_find:
                if item in i:
                    count1 += 1
                    if count1 == 4:
                        i = i.replace(item, find2)
                        count1 = 0
            tmp_list.append(i)
        for x in tmp_list:
            for item in to_find:
                if item in x:
                    brckt_list.append(x)
        total_brckt = len(brckt_list) - 1
        for z in tmp_list:
            for item in to_find:
                if item in z:
                    count2 += 1
                    if count2 == total_brckt:
                        z = z.replace(find2, find1)
            new_tmp.append(z)
        for line in new_tmp:
            writefile.write(line)

top_bottom(loc_json)
remove_warnings(loc_json, outputfile)
remove_uncreachable(outputfile, loc_json)
find_hostname(loc_json, outputfile,)
remove_success(outputfile, loc_json)
the_brackets('}', '},', loc_json, outputfile)
    
def load_csv(json_load, final_out): # This function simply outputs the data from the JSON file into a CSV format like text file
    find_list = ['#']
    find_list2 = ['*']
    tmp_hash = ''
    tmp_usr = ''
    with open(json_load) as jsonload, open(final_out, 'w') as txt_x:
        data = json.load(jsonload) #Load the data and expect a JSON format - which will give key, value pairs
        header = ("Hostname, Cron Jobs, Comments, User" + '\n') #Create the headers in the text file which will operate as Column headers in csv         
        txt_x.write(header)
        for i in data.items():
            lines_c = i[1]['ansible_facts']['ansible_local']['ansible_cron2']['Cron_Jobs'] # Get's the line from the JSON and stores it in lines_c
            x = lines_c.split(", ") # Splits the line based on commmas
            for r in x: #For each 'split' in the variable x
                for word in find_list: #If the 'word' which is a # is in r - then store it in tmp_hash
                    if word in r:
                        tmp_hash = r # See? We're storing here in tmp_hash if the line we split has a # in it
                    elif not any(x in find_list2 for x in r):
                        tmp_usr = r                
                    else:                   
                        if len(r) != 0: # Check to see if r contains no value - if it does contain something - continue to the following below
                            export = i[0] + ',' + r + ',' + tmp_hash + ',' + tmp_usr #Put the data in the variable export - and include i[0] which will be
                            txt_x.write(export)                      #The key value/hostname, and then also include 'r' and also include after that
                            txt_x.write('\n')                        #any comments that started with a # that we stored in tmp_hash
    print('The file has been generated at ' + txt_out)          

load_csv(outputfile, txt_out)

# We can check the string and see if contains a * or a 1-99 or a # and if it doesnt, it must be the user
# Question is where to insert this into the function load_csv
