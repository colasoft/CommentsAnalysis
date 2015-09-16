# -*- coding: utf-8 -*-
from __future__ import division  
from tgrocery import Grocery
import os
import re
import sys
import json
import jieba
import codecs
import string
import operator 

reload(sys)
sys.setdefaultencoding('utf8')
    
def is_chinese(uchar):
    if uchar >= u'\u4e00' and uchar<=u'\u9fa5':
       return True
    else:
       return False

def is_alphabet(uchar):
    if (uchar >= u'\u0041' and uchar<=u'\u005a') or (uchar >= u'\u0061' and uchar<=u'\u007a'):
       return True
    else:
       return False

def is_other(uchar):
    # if not (is_chinese(uchar) or is_number(uchar) or is_alphabet(uchar)):
    if not (is_chinese(uchar) or is_number(uchar)) :
       return True
    else:
       return False

def is_number(uchar):
    if uchar >= u'\u0030' and uchar<=u'\u0039':
       return True
    else:
       return False

def SymbolCut(ustring):
    ustring = ustring.decode('utf8')
    retList=[]
    utmp=[]
    for uchar in ustring:
        if is_other(uchar):
           if len(utmp)==0:
              continue
           else:
                retList.append("".join(utmp))
                utmp=[]
        else:
             utmp.append(uchar)
    if len(utmp)!=0:
       retList.append("".join(utmp))
    cutstr = ""
    for word in retList:
        cutstr = cutstr + (word + " ")
    return cutstr

def FileCounter(dirname,filter_types=[]):
     count=0
     filter_is_on=False
     if filter_types!=[]: filter_is_on=True
     for item in os.listdir(dirname):
         abs_item=os.path.join(dirname,item)
         if os.path.isdir(abs_item):
             count+=file_count(abs_item,filter_types)
         elif os.path.isfile(abs_item):
             if filter_is_on:
                 extname=os.path.splitext(abs_item)[1]
                 if extname in filter_types:
                     count+=1
             else:
                 count+=1
     return count

def GetJDPicSrc(str):
    try:
        start_int = str.index("src=\'http://")
        end_int = str.index("\' />",start_int)
        PicSrc = str[(start_int + 5) : end_int]
        str = str[end_int : len(str)]
        return PicSrc + " " + GetJDPicSrc(str)
    except:
	return " "

def StrRepetitionCheck(checkstr,per):
    words = jieba.cut(checkstr)
    pseg_str = ""
    word_all = 0
    tmpdit = {}
    for word in words:
        word_all = word_all + 1
        pseg_str = pseg_str + (word + ",")
        if tmpdit.has_key(word):
           count_word = int(tmpdit[word]) + 1
           tmpdit[word] = count_word
        else:
           tmpdit[word]  = 1
    word_list = sorted(tmpdit.iteritems(), key=operator.itemgetter(1),reverse=True )
    str_all = ""
    for index,item in enumerate(word_list):
        str_symptom = str(item).replace("u\'","\'")  
        str_tmp = str_symptom.decode("unicode-escape")  
        str_tmp = str_tmp[1 : (len(str_tmp)-1)]
        str_tmp = str_tmp.replace("\'","")
        word_count = int((str_tmp[(str_tmp.find(",") + 1):]).replace(" ",""))
        word_per = int((word_count*100)/word_all)
        str_all = (str_tmp + ":" + str(word_per)) + str_all
        if word_per >= per: 
           return False
    return True 

def ClassifyComments(text,comments_str):
    for item in text:
	if(len(item) > 3) and (True == StrRepetitionCheck(item,50)):  
           tmp = new_grocery.predict(item)
	   if not noSymbolComment:
				  break
           otherTypeMark = 0
           for d,x in tmp.dec_values.items():
               if(x >= 0.7):
                  otherTypeMark = 1
                  TypeMarkItem = "<"+d+">" + str(item) + "</"+d+">"
                  if TypeMarkItem not in comments_str:
                     comments_str = comments_str.replace(item,TypeMarkItem)
           if otherTypeMark == 0:
              TypeMarkItem = "<oth>" + str(item) + "</oth>"
              if TypeMarkItem not in comments_str:
                 comments_str = comments_str.replace(item,TypeMarkItem)
    return comments_str		   

if __name__ == "__main__":

   grocery = Grocery("/home/colasoft/myproject/wb/JDComments")
   train_dir = "/home/colasoft/myproject/wb/train"
   train_files = os.listdir(train_dir)
   train_src = []

   for train_name in train_files:
       train_fullname=os.path.join(train_dir,train_name)
       train_file = open(train_fullname)
       while 1:
	       train_line = train_file.readline()
	       train_src.append([train_name,train_line])
	       if not train_line:
			   break

   grocery.train(train_src)
   grocery.save()

   new_grocery = Grocery("/home/colasoft/myproject/wb/JDComments")
   new_grocery.load()
   
   orgComRoot = "/home/colasoft/myproject/OriginalComment/"
   merchant = sys.argv[1]

   Topkey  = "ClassifyComments"
   Key_1   = "CommentDetail"
   Key_2_text = "Text"
   Key_2_time = "Time"
   Key_2_pic = "Pic"

   if "JD" == merchant: 
      filecount = FileCounter(orgComRoot + merchant)
      analysisfile = 0
      bar_length=50
      
      for root, dirs, files in os.walk( orgComRoot + merchant ):
          for fn in files:
              jsonfilepath = root + "/" + fn 
              analysisfile += 1
              percent = (analysisfile/filecount) * 100
              hashes = '#' * int(percent/100.0 * bar_length)
              spaces = ' ' * (bar_length - len(hashes))
              sys.stdout.write("\rPercent: [%s] %d%%"%(hashes + spaces, percent))
              sys.stdout.flush()
	      if "~" in jsonfilepath:
	         continue
	      else:
                   productID =  fn[(fn.find("p-") + 2):fn.find("-s-")]
                   productID_path = "/home/colasoft/myproject/FinAnalysis/" + merchant + "/" + productID
	           if os.path.exists(productID_path):
	              comItem_f = file(productID_path)
                      old_jsonVal = json.load(comItem_f) 
                      comItem_f.close 
                      old_com_count = len(old_jsonVal[Topkey])
                      new_dict1 = old_jsonVal[Topkey]                   
                      orgjsonfile = file(jsonfilepath)
	              orgjsonobj = json.load(orgjsonfile)   
	              for comments_count in range(len(orgjsonobj["comments"])):
	                  comments_str = orgjsonobj["comments"][comments_count]["content"].encode("utf-8")
                          comments_time= orgjsonobj["comments"][comments_count]["creationTime"].encode("utf-8")
		          noSymbolComment = SymbolCut(comments_str)
                          noSymbolComment = noSymbolComment.replace("\r\n"," ")
                          if(len(noSymbolComment) > 0):
		             text = noSymbolComment.split(' ')
                             MarkComment = ClassifyComments(text,comments_str)	   
                             new_dict_2 = {Key_2_text:MarkComment,Key_2_time:comments_time}             
                          if orgjsonobj["comments"][comments_count].has_key("showOrderComment"):
                             try:        
                                 picContent = (orgjsonobj["comments"][comments_count]["showOrderComment"]["content"]).encode("utf-8")
                                 PicSrc = GetJDPicSrc(picContent)
                                 new_dict_2[Key_2_pic] = PicSrc                                                   
                             except:
			            pass
                          new_dict1[str(old_com_count)] = new_dict_2
                          old_com_count = old_com_count + 1
                      new_dict = {Topkey:new_dict1}   
                      new_json_obj = json.dumps(new_dict) 
                      comItem_f = open(productID_path,"w")                       
                      comItem_f.write(new_json_obj)
                      orgjsonfile.close
                      comItem_f.close 
                   else:
		      comItem_f = open(productID_path, "w") 
                      orgjsonfile = file(jsonfilepath)
	              orgjsonobj = json.load(orgjsonfile) 
                      dict1={}
	              for comments_count in range(len(orgjsonobj["comments"])):
	                  comments_str = orgjsonobj["comments"][comments_count]["content"].encode("utf-8")
                          comments_time= orgjsonobj["comments"][comments_count]["creationTime"].encode("utf-8")
		          noSymbolComment = SymbolCut(comments_str)
                          noSymbolComment = noSymbolComment.replace("\r\n"," ")
                          if(len(noSymbolComment) > 0):
		             text = noSymbolComment.split(' ')
                             MarkComment = ClassifyComments(text,comments_str)	
                             dict2 = {Key_2_text:MarkComment,Key_2_time:comments_time}             
                          if orgjsonobj["comments"][comments_count].has_key("showOrderComment"):
                             try:        
                                 picContent = (orgjsonobj["comments"][comments_count]["showOrderComment"]["content"]).encode("utf-8")
                                 PicSrc = GetJDPicSrc(picContent)
                                 dict2[Key_2_pic] = PicSrc                                                     
                             except:
			            pass
                          dict1[str(comments_count)] = dict2
                      dictTop= {Topkey : dict1}
                      json_ClassifyCom = json.dumps(dictTop)
                      comItem_f.write(json_ClassifyCom)
                      orgjsonfile.close
                      comItem_f.close
      print"\r\n"                     

   if "GM" == merchant:
      filecount = FileCounter(orgComRoot + merchant)
      analysisfile = 0
      bar_length=50
      
      for root, dirs, files in os.walk( orgComRoot + merchant ):
          for fn in files:
              jsonfilepath = root + "/" + fn 
              analysisfile += 1
              percent = (analysisfile/filecount) * 100
              hashes = '#' * int(percent/100.0 * bar_length)
              spaces = ' ' * (bar_length - len(hashes))
              sys.stdout.write("\rPercent: [%s] %d%%"%(hashes + spaces, percent))
              sys.stdout.flush()
	      if "~" in jsonfilepath:
	         continue
	      else:
                   productID =  fn[(fn.find("p-") + 2):fn.find("-s-")]
                   productID_path = "/home/colasoft/myproject/FinAnalysis/" + merchant + "/" + productID
	           if os.path.exists(productID_path):
	              comItem_f = file(productID_path)
                      old_jsonVal = json.load(comItem_f) 
                      comItem_f.close 
                      old_com_count = len(old_jsonVal[Topkey])
                      new_dict1 = old_jsonVal[Topkey]                   
                      orgjsonfile = file(jsonfilepath)
	              orgjsonobj = json.load(orgjsonfile)   
                      for comments_count in range(len(orgjsonobj["evaList"]["Evalist"])):
	                  comments_str = orgjsonobj["evaList"]["Evalist"][comments_count]["appraiseElSum"]
                          comments_time= orgjsonobj["evaList"]["Evalist"][comments_count]["post_time"]
		          noSymbolComment = SymbolCut(comments_str)
                          noSymbolComment = noSymbolComment.replace("\r\n"," ")
                          if(len(noSymbolComment) > 0):
		             text = noSymbolComment.split(' ')
                             MarkComment = ClassifyComments(text,comments_str)	   
                             new_dict_2 = {Key_2_text:MarkComment,Key_2_time:comments_time}                       
                          if(len(orgjsonobj["evaList"]["Evalist"][comments_count]["pic"]) > 0):
                             try:        
                                 picContent = "".join(orgjsonobj["evaList"]["Evalist"][comments_count]["pic"])
                                 new_dict_2[Key_2_pic] = picContent                                                     
                             except:
			            pass  
                          new_dict1[str(old_com_count)] = new_dict_2
                          old_com_count = old_com_count + 1
                      new_dict = {Topkey:new_dict1}   
                      new_json_obj = json.dumps(new_dict) 
                      comItem_f = open(productID_path,"w")                       
                      comItem_f.write(new_json_obj)
                      orgjsonfile.close
                      comItem_f.close 
                   else:
		      comItem_f = open(productID_path, "w") 
                      orgjsonfile = file(jsonfilepath)
	              orgjsonobj = json.load(orgjsonfile)  
                      dict1={}                    
                      for comments_count in range(len(orgjsonobj["evaList"]["Evalist"])):
	                  comments_str = orgjsonobj["evaList"]["Evalist"][comments_count]["appraiseElSum"]
                          comments_time= orgjsonobj["evaList"]["Evalist"][comments_count]["post_time"]
		          noSymbolComment = SymbolCut(comments_str)
                          noSymbolComment = noSymbolComment.replace("\r\n"," ")
                          if(len(noSymbolComment) > 0):
		             text = noSymbolComment.split(' ')
                             MarkComment = ClassifyComments(text,comments_str)	
                             dict2 = {Key_2_text:MarkComment,Key_2_time:comments_time}             
                          if(len(orgjsonobj["evaList"]["Evalist"][comments_count]["pic"]) > 0):
                             try:        
                                 picContent = "".join(orgjsonobj["evaList"]["Evalist"][comments_count]["pic"])
                                 dict2[Key_2_pic] = picContent                                                     
                             except:
			            pass  
                          dict1[str(comments_count)] = dict2
                      dictTop= {Topkey : dict1}
                      json_ClassifyCom = json.dumps(dictTop)
                      comItem_f.write(json_ClassifyCom)
                      orgjsonfile.close
                      comItem_f.close 
      print"\r\n"     

   if "SN" == merchant:
      filecount = FileCounter(orgComRoot + merchant)
      analysisfile = 0
      bar_length=50
      
      for root, dirs, files in os.walk( orgComRoot + merchant ):
          for fn in files:
              jsonfilepath = root + "/" + fn 
              analysisfile += 1
              percent = (analysisfile/filecount) * 100
              hashes = '#' * int(percent/100.0 * bar_length)
              spaces = ' ' * (bar_length - len(hashes))
              sys.stdout.write("\rPercent: [%s] %d%%"%(hashes + spaces, percent))
              sys.stdout.flush()
	      if "~" in jsonfilepath:
	         continue
	      else:
   		   print merchant + ":" + jsonfilepath
                   productID =  fn[(fn.find("-000000000") + 10):fn.find("--")]
                   productID_path = "/home/colasoft/myproject/FinAnalysis/" + merchant + "/" + productID
	           if os.path.exists(productID_path):
	              comItem_f = file(productID_path)
                      old_jsonVal = json.load(comItem_f) 
                      comItem_f.close 
                      old_com_count = len(old_jsonVal[Topkey])
                      new_dict1 = old_jsonVal[Topkey]                   
                      orgjsonfile = file(jsonfilepath)
	              orgjsonobj = json.load(orgjsonfile)   
                      for comments_count in range(len(orgjsonobj["commodityReviews"])):
	                  comments_str = orgjsonobj["commodityReviews"][comments_count]["content"]
                          comments_time= orgjsonobj["commodityReviews"][comments_count]["publishTime"]
		          noSymbolComment = SymbolCut(comments_str)
                          noSymbolComment = noSymbolComment.replace("\r\n"," ")
                          if(len(noSymbolComment) > 0):
		             text = noSymbolComment.split(' ')
                             MarkComment = ClassifyComments(text,comments_str)	   
                             new_dict_2 = {Key_2_text:MarkComment,Key_2_time:comments_time}                       
                          if(orgjsonobj["commodityReviews"][comments_count].has_key("imageinfo")):           
                             try:        
                                 for pic_count in range(len(orgjsonobj["commodityReviews"][comments_count]["imageinfo"])):
                                     picContent += (orgjsonobj["commodityReviews"][comments_count]["imageinfo"][pic_count] + "_400x400.jpg")
                                 new_dict_2[Key_2_pic] = picContent                                                     
                             except:
			            pass  
                          new_dict1[Key_1 + str(old_com_count)] = new_dict_2
                          new_dict = {Topkey:new_dict1}   
                      new_json_obj = json.dumps(new_dict) 
                      comItem_f = open(productID_path,"w")                       
                      comItem_f.write(new_json_obj)
                      orgjsonfile.close
                      comItem_f.close 
                   else:
		      comItem_f = open(productID_path, "w") 
                      orgjsonfile = file(jsonfilepath)
	              orgjsonobj = json.load(orgjsonfile)                      
                      for comments_count in range(len(orgjsonobj["commodityReviews"])):
	                  comments_str = orgjsonobj["commodityReviews"][comments_count]["content"]
                          comments_time= orgjsonobj["commodityReviews"][comments_count]["publishTime"]
		          noSymbolComment = SymbolCut(comments_str)
                          noSymbolComment = noSymbolComment.replace("\r\n"," ")
                          if(len(noSymbolComment) > 0):
		             text = noSymbolComment.split(' ')
                             MarkComment = ClassifyComments(text,comments_str)	   
                             new_dict_2 = {Key_2_text:MarkComment,Key_2_time:comments_time}                       
                          if(orgjsonobj["commodity,Reviews"][comments_count].has_key("imageinfo")):           
                             try:        
                                 for pic_count in range(len(orgjsonobj["commodityReviews"][comments_count]["imageinfo"])):
                                     picContent += (orgjsonobj["commodityReviews"][comments_count]["imageinfo"][pic_count] + "_400x400.jpg")
                                 new_dict_2[Key_2_pic] = picContent                                                     
                             except:
			            pass
                      dict1  = {(Key_1 + str(0)) : dict2}
                      dictTop= {Topkey : dict1}
                      json_ClassifyCom = json.dumps(dictTop)
                      comItem_f.write(json_ClassifyCom)
                      orgjsonfile.close
                      comItem_f.close           
      print"\r\n"           
		
