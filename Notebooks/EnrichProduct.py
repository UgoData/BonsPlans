#!/usr/bin/env python
# -*- coding: utf-8 -*-

### Import des libraries  ###
import pandas as pd, numpy as np
import json, requests
import re
import unicodedata
import itertools


### Recuperation des temps de trajet ###
	
def fuseLatLong(row):
	"""Fusion de la latitude et de la longitude. Format Google comma separated"""
	return str(row['latMagasin'])+','+str(row['longMagasin'])
	

def mygrouper(n, iterable):
    args = [iter(iterable)] * n
    return ([e for e in t if e != None] for t in itertools.izip_longest(*args))

def getTempsTrajetTemp(df,latlong_origin,modes):
    """Obtention du temps de trajet avec lAPI Google"""
    # Get origin and destination : unique lat_long
    list_dest=[str(i) for i in df['magLatLong'].unique()]
    result_latlong=pd.DataFrame(columns=modes)

    for mode in modes:
        list_of_list=list(mygrouper(25, list_dest))
        count=0
        for y in list_of_list:
            str_dests='|'.join(y)
            #str1="https://maps.googleapis.com/maps/api/distancematrix/json?origins="+latlong_origin+"&destinations="+str_dests+"&mode="+mode+"&language=fr&sensor=false&key=AIzaSyCE6WGSUpQlkbrkTXXbe_ahfk79r0kkIVo"
            # Ugo's key
            str1="https://maps.googleapis.com/maps/api/distancematrix/json?origins="+latlong_origin+"&destinations="+str_dests+"&mode="+mode+"&language=fr&sensor=false&key=AIzaSyAw7VWZfZn0AUVeknT87QORTlZZxRIolZI"
            str2 = requests.get(str1,verify=False).json()
            for idx,i in enumerate(y):
                result_latlong.loc[count,'magLatLong']=i
                try:
                    result_latlong.loc[count,mode]=str2['rows'][0]['elements'][idx]['duration']['value']
                except:
                    print 'Probleme with API Google :', str1
                    result_latlong.loc[count,mode]=999999
                count+=1
    return result_latlong
	

# Merge the distinct latlong with full dataset
def getTpsTrajet(product_info,latlong_origin,modes):
	"""Rajout des temps de trajet au df des produits

	Args:
		df: DataFrame avec les informations sur les produits et les magasins
		latlong_origin: Origine de lutilisateur
		modes: liste des modes de transport de lutilisateur

	Returns:
		Mise a jour de df
	"""
	df2=getTempsTrajetTemp(product_info,latlong_origin,modes)
	return pd.merge(product_info,df2,on='magLatLong', how='left')
	


### Enrichissement sur les unites et les quantites ###
def getUnit(str1):
	"""Recuperation des unites des produits

	Args:
		str1: description du produit qui est censee contenir lunite et la quantite

	Returns:
		unite en minuscule
	"""
	try:
		# double quantite espace
			unit=re.search('\d+(\D{1,10})$',str1).group(1)
	except:
		try:
			#print(1)
			# quantite espace
			unit=re.search('\d +(\D{1,10})$',str1).group(1)
		except AttributeError :
			try:
				#print(2)
				# quantite & unit merged
				unit=re.search('\d+(\D{1,10})+$',str1).group(1)
			except:
				try:
					#print(3)
					# no unit
					unit=re.search('\d+()+$',str1).group(1)
				except:
					try:
						#print (4)
						unit=re.search('\d+,+\d+(\D{1,10})',str1).group(1)
					except:
						try:
							#print (5)
							unit=re.search('\d+(\D{1,10})',str1).group(1)
						except:
							unit=''
	#print unit
	return unit.lower()



def dictUnit(x):
	"""objectif de mettre tout dans une meme unite

	Args:
		x: unite recuperer plus haut

	Returns:
		valeur a multiplier avec la quantite pour avoir quelque chose d'uniforme
	"""
	# Unit dictionnary
	unit_dict={'l':1,'dl':0.1,'cl':0.01,'ml':0.001,'':1,'g':0.001,'kg':1}
	
	try:
		result=unit_dict[x]
	except:
		result=1
	return result

# Get quantite
def getQuantity(str1):
	"""Recuperation de la quantite de produit"""
	try:
		# quantite espace
		quantityTemp=re.sub('[^\d,]+','*',str1)
		quantity=re.sub('^[*]|[*]$','',quantityTemp)

		if ',*' in quantity:
			#print(quantity)
			quantity=eval(re.search('[,|-][\D|\S](\d+)',quantity).group(1))
		else:
			quantity=eval(quantity.replace(',','.'))
			
	except AttributeError:
		# quantite unit merged
		print "Probleme avec la recuperation de la quantite %s" % str1
	except SyntaxError:
		quantity=1
	return quantity
	
	
### Enrichissement sur le positionnement prix du produit ###
def pct_rank_qcut(series, n):
	edges = pd.Series([float(i) / n for i in range(n + 1)])
	f = lambda x: (edges >= x).argmax()
	return series.rank(pct=1).apply(f)
	

### Enrichissement sur le positionnement prix du produit ###
def qcut_custom(df,nb_class):
	"""Positionnement du produit parmi les retours"""
	result=1
	try:
		result=pd.qcut(df, nb_class,labels=range(1,nb_class+1))
	except ValueError:
		print 'value error for %s' % df
	except AttributeError:
		print 'attribute error for %s' % df
	return result

### Reduction type ###
def getReducType(row):
	"""Classification des types de reduction en fonction du libelle"""
	var=row.lower()
# Cas reduction sur carte de fidelite
	if 'carte' in var:
		var='carte'        
# Cas deuxieme en reduction
	elif '2eme' in var or '2ieme' in var or '2ème' in var or '3ième' in var:
		var='2iemGrat'

# Cas troisieme en reduction
	elif '3eme' in var or '3ieme' in var or '3ème' in var or '3ième' in var:
		var='3iemGrat'

# Cas reduction immediate
	elif var=='':
		var='noreduc'

# Cas autres
	else:
		var='autres'
	return var


### Time transformation ###
def timeTransformation(x):
	"""Convertion des temps de trajet en seconde en score."""
	#var=math.log(1/(x/(60*3))+1)
	if x<(60*5):
		var=1
	elif x<(60*10):
		var=0.75
	elif x<(60*15):
		var=0.5
	elif x<(60*20):
		var=0.25
	else:
		var=0
	return var
	


### Pourcentage et montant des reductions ###
def pctReduc(row):
	prix_avantreduc=row['offrePrix']
	prix_apresreduc=row['prix_old']
	try :
		var=(prix_apresreduc/prix_avantreduc)-1
	except:
		var=0
	return var

def mntReduc(row):
	prix_avantreduc=row['offrePrix']
	prix_apresreduc=row['prix_old']
	try :
		var=prix_apresreduc-prix_avantreduc
	except:
		var=0
	return var

### User category ###
def getAnalyticsUserCategory(row,user_info,regex):
	var=0
	try:
		for cat in regex.sub('', row['analytics_category']).split(','):
			if user_info.loc[0,'universConso_'+str(cat)]>0:
				var=1
	except:
		var=0
	return var

### Sensitivity to reduction for the user ###
def reduc_scoring(row,user_info,regex):
	var=[]
	try:
		for cat in regex.sub('', row['analytics_category']).split(','):
			var.append(user_info.loc[0,'reductionSens_'+str(cat)+'_'+row['reduc_type']])
	except:
		var=[]
	return np.mean(var)

### Price unit calculation ###
def priceUnit(row):
        try:
                var=row['offrePrix']/row['quantite_unite']
        except:
                var=99999.0
        return var

### Bio or dietetique
def bio(row):
        r=row['libelle']+' '+row['offreLib']+' '+row['offreDesc']
        result=0
        if ('bio' in r.lower() )| (re.search('( ab$| ab )', r.lower()) is not None)| ('gluten' in r.lower()) :
                result=1
        return result

### Bio or dietetique
def defineBio(row,id_cat):
        result=0
        if (row['bio']==1) &  (id_cat in row['analytics_category_list']):
                result=1
        return result

### Define if lowPrice or highPrice
def defineLowHighPrice(row, seuil_min, seuil_max, id_cat):
        result=0
        if (row['quantile_prixquantite']>=seuil_min) & (row['quantile_prixquantite']<seuil_max) & (id_cat in row['analytics_category_list']):
                result=1
        return result

### Define if reductype
def defineReducType(row, id_cat, type_reduc):
        """Classification des types de reduction en fonction du libelle"""
        result=0
# Cas reduction sur carte de fidelite
        if (row['reduc_type']==type_reduc) & (id_cat in row['analytics_category_list']):
                result=1
        return result

### Get magasin
def getMagasin(x):
        if 'monop' in x.lower():
                result='monop'
        elif 'carrefour' in x.lower():
                result='carrefour'
        elif 'fnac' in x.lower():
                result='fnac'
        else:
                result='other'
        return result

### Take best price_unit
def bestPriceUnit(row):
    result=row['price_unit']
    if row['prixUnit']!='':
        result=row['prixUnit']
    return float(result)