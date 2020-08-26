import random
import json
from bs4 import BeautifulSoup as bs
import requests
import threading
import psycopg2
from nltk.tag.stanford import StanfordNERTagger,StanfordPOSTagger
import re

class AutomaticCrosswordGeneration:

	def __init__(self,topic_name):
		self.conn = psycopg2.connect("dbname='dwdb' user='postgres' host='localhost' password='root'")
		self.cursor = self.conn.cursor()
		self.traverse_level = 3
		self.topic_name = topic_name
		self.word_traverse_list = {}
		self.mword_traverse_list = {}
		pattern_path = "c://users/rojit/desktop/cwpts.json"
		patterns = json.loads(open(pattern_path,"r").read())["patterns"]
		self.scaffold =patterns[random.randrange(0,len(patterns))]
		self.oscaffold = self.scaffold
		self.max_word_bounds = 0
		if len(self.scaffold) == len(self.scaffold[0]):
			self.max_word_bounds = len(self.scaffold)
		elif len(self.scaffold) < len(self.scaffold[0]):
			self.max_word_bounds = len(self.scaffold)
		else:
			self.max_word_bounds = len(self.scaffold[0])
		self.len_word_dict = {}
		self.max_traverse_list_len = 20000
		self.word_defs = {}
		self.acrosses = []
		self.downs = []


	def traverse_wikis(self,url,level):
		
		if "https://" not in url and "www" not in url:
			url = "https://en.wikipedia.org/wiki/"+url
		try:
			url_topic_text = url.replace("https://en.wikipedia.org/wiki/","")
			if "_" in url_topic_text:
				url_topic_text = url_topic_text.replace("_","")
			url_topic_text = url_topic_text.encode().decode("ascii")
			if "(" in url_topic_text:
				url_topic_text = url_topic_text[0:url_topic_text.index("(")]
			symbols = "!@$%^&*()_+-={}|:\"<>?[]\\;',./'1234567890"
			is_symbol_present = False
			for s in symbols:
				if s in url_topic_text:
					is_symbol_present = True
					break
			if len(url_topic_text.split(" ")) <= 2 and len(url_topic_text) <= self.max_word_bounds and is_symbol_present == False and len(url_topic_text) >= 3:
				# print(url.encode(),url_topic_text.encode(),end="\r")
				print(str(len(self.word_traverse_list))+"/"+str(self.max_traverse_list_len),end="\r")
				self.word_traverse_list[url_topic_text.lower()] = url
				if len(url_topic_text.lower()) not in self.len_word_dict:
					self.len_word_dict[len(url_topic_text.lower())] = [url_topic_text.lower()]
				else:
					self.len_word_dict[len(url_topic_text.lower())].append(url_topic_text.lower())
		except:
			lol=1


		if len(self.word_traverse_list) >= self.max_traverse_list_len:
			return 1
		if level <= self.traverse_level:
			try:
				soup = bs(requests.get(url).content,"html.parser")
			except:
				soup = bs(requests.get(url).content,"html.parser")
			main = soup.find_all(lambda tag:tag.name=="div" and tag.get("id")!=None and "mw-content-text" in tag.get("id"))[0]
			anchors = [ a.get("href") for ps in main.find_all("p") for a in ps.find_all(lambda tag:tag.name=="a" and tag.get("href")!=None and "/wiki/" in tag.get("href") and ":" not in tag.get("href"))]
			random.shuffle(anchors)
			for a in anchors:
				b = self.traverse_wikis("https://en.wikipedia.org"+a,level+1)
				if b == 1:
					return 1


	def get_word_defs(self):
		for w in self.mword_traverse_list:
			url = self.mword_traverse_list[w]
			if w not in self.word_defs:
				soup = bs(requests.get(url).content,"html.parser")
				main = soup.find_all(lambda tag:tag.name=="div" and tag.get("id")!=None and "mw-content-text" in tag.get("id"))[0]
				text = main.find_all(lambda tag:tag.name=="p" and len(tag.text) > 10)[0].text
				self.word_defs[w] = text


	def print_scaffold(self):
		for i in self.scaffold:
			print(i)

	def decide_word(self,construct):
		c_len = len(construct)
		try:
			len_word_list = self.len_word_dict[c_len]
		except:
			return ""
		index_list = {}
		for i in range(c_len):
			if construct[i] != "0":
				index_list[i] = construct[i]
		if len(index_list) > 0:
			for w in len_word_list:
				matches = True
				for i in index_list:
					if w[i] != construct[i]:
						matches = False
						break
				if matches == True:
					self.mword_traverse_list[w] = self.word_traverse_list[w]
					return w
		else:
			word = self.len_word_dict[c_len][random.randrange(len(self.len_word_dict[c_len]))]
			return word

		if len(index_list) > 0:
			wildcard_string = ["_" for i in range(c_len)]
			for i in index_list:
				wildcard_string[i] = construct[i]
			wildcard_string = "".join(wildcard_string)

			self.cursor.execute("select word,meanings from words_meanings where word like %s and unfindable=0 and ('noun'=any(types) or 'adjective'=any(types) or 'verb'=any(types) or 'adverb'=any(types));",(wildcard_string,))
			res = self.cursor.fetchall()
			if len(res) > 0:
				ridx = random.randrange(len(res))
				self.word_defs[res[ridx][0]] = ". ".join(res[ridx][1])
				return res[ridx][0]

		return ""

	def fill_scaffold(self):
		for i in range(0,len(self.scaffold)):
			for j in range(0,len(self.scaffold[i])):
				block = self.scaffold[i][j]
				if block != 1:
					down_len = 1
					down_construct = str(block)
					down_start = i
					#go front
					for k in range(i+1,len(self.scaffold)):
						if self.scaffold[k][j] != 1:
							down_len += 1
							down_construct = down_construct + str(self.scaffold[k][j])
						else:
							break
					#go back
					for k in range(i-1,-1,-1):
						if self.scaffold[k][j] != 1:
							down_len += 1
							down_start = k
							down_construct = str(self.scaffold[k][j])+down_construct
						else:
							break
					if down_len != 0 and "0" in down_construct and len(down_construct) >= 3:
						word = self.decide_word(down_construct)
						word_i = 0
						if word != "":
							for k in range(down_start,down_start+down_len):
								self.scaffold[k][j] = word[word_i]
								word_i += 1
						else:
							for k in range(down_start,down_start+down_len):
								if self.scaffold[k][j] == 0:
									self.scaffold[k][j] = "-"
						self.downs.append([word,(down_start,j)])
					across_len = 1
					across_construct = str(block)
					across_start = j
					for k in range(j+1,len(self.scaffold[i])):
						if self.scaffold[i][k] != 1:
							across_len += 1
							across_construct = across_construct + str(self.scaffold[i][k])
						else:
							break
					for k in range(j-1,-1,-1):
						if self.scaffold[i][k] != 1:
							across_len += 1
							across_start = k
							across_construct = str(self.scaffold[i][k])+across_construct
						else:
							break	
					if across_len != 0 and "0" in across_construct and len(across_construct) >= 3:
						word = self.decide_word(across_construct)
						word_i = 0
						if word != "":
							for k in range(across_start,across_start+across_len):
								self.scaffold[i][k] = word[word_i]
								word_i += 1
						else:
							for k in range(across_start,across_start+across_len):
								if self.scaffold[i][k] == 0:
									self.scaffold[i][k] = "-"
						self.acrosses.append([word,(i,across_start)])


	def remove_impurities(self):
		for i in range(len(self.scaffold)):
			for j in range(len(self.scaffold[0])):
				if self.scaffold[i][j] == "-":
					self.scaffold[i][j] = 1
		for a in self.acrosses:
			if a[0] == "":
				self.acrosses.remove(a)
		for a in self.downs:
			if a[0] == "":
				self.downs.remove(a)



	def get_empty_scaffold(self):
		self.oscaffold = [[0 for j in range(len(self.scaffold[0]))] for i in range(len(self.scaffold))]
		for i in range(len(self.scaffold)):
			for j in range(len(self.scaffold[0])):
				if self.scaffold[i][j] != 1:
					self.oscaffold[i][j] = 0
				else:
					self.oscaffold[i][j] = 1

	def process_word_defs(self):
		n_sentence = 1
		for word in self.word_defs:
			word_def_text = self.word_defs[word]
			refs = re.findall(r"\[(.*?)\]",word_def_text)
			for ref in refs:
				word_def_text = word_def_text.replace("["+ref+"]","")
			sens = word_def_text.split(". ")
			if len(sens) > n_sentence:
				sens = sens[0:n_sentence]
			from_words = ["is","are","was","refers"]
			for k in range(len(sens)):
				s = sens[k]
				word_tokens = s.split(" ")
				from_found = False
				min_from_index = 99999
				for f in from_words:
					if f in word_tokens:
						i = word_tokens.index(f)
						if min_from_index > i:
							min_from_index = i
				if min_from_index <= 10:
					sens[k] = " ".join(word_tokens[min_from_index+1::])
				else:
					for j in range(len(word_tokens)):
						if word_tokens[j] in word or word in word_tokens[j]:
							word_tokens[j] = "___"
					sens[k] = " ".join(word_tokens)
			self.word_defs[word] = ". ".join(sens)


	def generate_crossword_repr(self):
		print("Constructing word list.....")
		self.traverse_wikis(self.topic_name,1)
		print("Building crossword....")
		self.fill_scaffold() #get and decides match words, clusters them in acrosses and downs with coords
		print("Getting word defs....")
		self.get_word_defs()
		print("Fitting grid with obtained words...")
		self.remove_impurities()
		self.get_empty_scaffold()
		self.process_word_defs()
		print(self.oscaffold)
		print(self.scaffold)
		print(self.acrosses)
		print(self.downs)
		print(str(self.word_defs).encode())
		parcel = {"original_scaffold":self.oscaffold,"filled_scaffold":self.scaffold,"across_words":self.acrosses,"down_words":self.downs,"word_defs":self.word_defs}
		return parcel
		


AutomaticCrosswordGeneration("Albert Einstein").generate_crossword_repr()
