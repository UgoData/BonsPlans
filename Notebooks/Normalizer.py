#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from nltk.corpus import stopwords
from nltk.stem.snowball import FrenchStemmer
import unicodedata


def normaliz(row,french_stopwords,reg_numb,reg_ponct,stemmer):
	""" Normalize Text """

	# to lower case
	str1=row.lower()
	#print 'low_case : ', str1

	# Suppress number
	str1=reg_numb.sub('', str1)
	#print 'only_letters : ', str1

	# Suppress punctuation
	str1=reg_ponct.sub('', str1)
	#print 'no_ponctuation : ', str1

	# Suppress stop words

	str1 = [token for token in str1.split(' ') if token.lower() not in french_stopwords]
	#print 'no_stop_words : ', str1

	# Suppress accent
	str1 = [unicodedata.normalize('NFD', unicode(word,'utf-8')).encode('ascii', 'ignore') for word in str1]    
	#print 'no_accent : ', str1

	# Stemming of words
	str1=[stemmer.stem(word) for word in str1]
	#print 'stemming : ', str1

	# Merging words
	str1=' '.join(str1)
	#print 'merge_list : ',str1

	return str1