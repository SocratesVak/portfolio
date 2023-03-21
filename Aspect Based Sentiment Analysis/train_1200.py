# -*- coding: utf-8 -*-
"""train_1200

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/156JSeqzld29AprFvKmFYfOU_6e_ShRAT
"""

import pandas as pd
import numpy as np
import pickle
import nltk
import glob
import re
from nltk.stem import WordNetLemmatizer
from sklearn.feature_selection import SelectKBest,chi2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn import svm, metrics
nltk.download('omw-1.4')
nltk.download('wordnet')
nltk.download('punkt')
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk import pos_tag
nltk.download('averaged_perceptron_tagger')



def train1200(array):

    """δίνουμε το μονοπάτι στον υπολογιστή, ώστε να αποκτήσει πρόσβαση στα συγκεκριμένα parts, που επιθυμούμε"""

    path = '.'
    filenames = glob.glob(path + f'/part{array}.xml')

    """Δημιουργούμε μεταβλητή, διαβάζουμε τα δεδομένα από όλα τα xml και τα συνενώνουμε"""

    read_df = []
    for filename in filenames:
        read_df.append(pd.read_xml(filename, xpath=".//sentence|.//Opinion"))
        df = pd.concat(read_df)

    """Αντικαθιστούμε τα άδεια κελιά στο column του text με τιμές από το πάνω κελί"""

    df['text'] = df['text'].replace('', np.nan).ffill()

    """ Διαγράφουμε τις αχρείαστες στήλες"""
    
    df.drop(["OutOfScope","Opinions",'target','from','to','id'], axis = 1, inplace = True)
    newdf = df.dropna()

    """δημιουργούμε τον πίνακα με τα features και τον πίνακα με τα target variables"""

    X_train=newdf[['text']].copy()
    y=newdf[['category','polarity']].copy()



    """μετατρέπουμε τα δεδομένα των target variables από κατηγορικά σε αριθμητικά, ώστε να μπορούν να διαβαστούν αποτελεσματικά από τον υπολογιστή
    #διατηρούμε, όμως, έναν τρόπο να αντιστοιχίζουμε τα αριθμητικά σε κατηγορικά"""

    le=LabelEncoder()
    y['category'] = le.fit_transform(y['category'])
    le_name_mapping = dict(zip(le.classes_, le.transform(le.classes_)))
    #print(len(le_name_mapping))
    y['polarity'] = le.fit_transform(y['polarity'])
    le_name_mapping = dict(zip(le.classes_, le.transform(le.classes_)))
    #print(len(le_name_mapping))
    





    """εδώ ορίζουμε τρεις συναρτήσεις για λόγους οικονομίας υπολογιστικού φόρτου. Η πρώτη αφαιρεί τα stopwords. Ταυτόχρονα δημιουργείται μια στήλη στο
    dataframe με τα features, η οποία θα περιλαμβάνει τις προτάσεις με την ίδια σειρά, αλλά καθαρισμένες."""
    X_train['Review_without_stopwords']= X_train['text'].copy()


    def rem_stopwords_tokenize(data,name):
      
      def getting(sent):
          example_sent = sent
          
          filtered_sentence = [] 

          stop_words = set(stopwords.words('english')) 

          word_tokens = word_tokenize(example_sent) 
          
          filtered_sentence = [w for w in word_tokens if not w in stop_words] 
          
          return filtered_sentence

      x=[]
      for i in data[name].values:
          x.append(getting(i))
      data[name]=x

    


    """εδώ προβαίνουμε σε μετασχηματισμό όλων των λέξεων στη λημματική τους μορφή."""
    def Lemmatization(data,name):
      lemmatizer = WordNetLemmatizer()

      def getting2(sent):
          
          example = sent
          output_sentence =[]
          word_tokens2 = word_tokenize(example)
          lemmatized_output = [lemmatizer.lemmatize(w) for w in word_tokens2]
          
          # Remove characters which have length less than 2  
          without_single_chr = [word for word in lemmatized_output if len(word) > 2]
          # Remove numbers
          cleaned_data_title = [word for word in without_single_chr if not word.isnumeric()]
          
          return cleaned_data_title

      x=[]
      for i in data[name].values:
          x.append(getting2(i))
      data[name]=x

      
    """ η τρίτη συνάρτηση κάνει POS tagging σε κάθε λέξη επίσης του κειμένου. Τα δεδομένα μας επιστρέφουν και πάλι σε μορφή νέας στήλης στο dataframe.
    Κάθε πρόταση από τις αρχικές έχει πλέον τρία αντίστοιχα της: 1.καθαρισμένη από stopwords_ 2.μετατροπή στη λημματική μορφή_ 3.κάθε λέξη της πρόταση 
    συνενωμένη με το αντίστοιχο της POS (π.χ. pizza/NN)"""


    def pos_tagging(data,name):

        def getting3(sen):
          example=sen
          tokens=word_tokenize(example)
          sent_tagged=nltk.pos_tag(tokens)
          return sent_tagged

        x=[]
        for i in data[name].values:
          x.append(getting3(i))

        new_text_pos_tagged=[]
        for sent in x:
          new_sent=[]
          for word in sent:
            new_word= word[0] + "/" + word[1]
            new_sent.append(new_word)
          new_text_pos_tagged.append(new_sent)

        data[name]=new_text_pos_tagged


    """Αυτή η συνάρτηση χρησιμεύει, ώστε να μετατρέψουμε τα εξαγόμενα των 3 προηγούμενων συναρτήσεων σε συνεχή λόγο. Έτσι, αποκαθίσταται η ροή της πρότασης,
    ώστε να υπάρχει μια αντιστοίχιση με την "αυθεντική" πρόταση"""
    def make_sentences(data,name):
      data[name]=data[name].apply(lambda x:' '.join([i+' ' for i in x]))
      # Removing double spaces if created
      data[name]=data[name].apply(lambda x:re.sub(r'\s+', ' ', x, flags=re.I))






    rem_stopwords_tokenize(X_train,name='Review_without_stopwords')
    make_sentences(X_train,'Review_without_stopwords')

    """το εξαγόμενο της συνάρτησης που αφαιρεί τα stopwords χρησιμοποιείται ως εισαγόμενο για τη συνάρτηση που μας δίνει τα λήμματα των λέξεων. Μετά
    αφαιρείται ως αχρείαστη"""

    X_train['After_Lemmatization']=X_train['Review_without_stopwords'].copy()
    X_train.drop(["Review_without_stopwords"], axis = 1, inplace = True)
    Lemmatization(X_train,name='After_Lemmatization')
    make_sentences(X_train,'After_Lemmatization')

    """Αντίστοιχα, ως εισαγόμενο της συνάρτησης που μας δίνει τα POS χρησιμοποιούμε τη συνάρτηση που μας έχει δώσει τα λήμματα. Δε χρειαζόμαστε
    τα μέρη του λόγου των stopwords. Με αυτόν τον τρόπο καθαρίζουμε το κείμενο μας"""
    X_train['POS_tags']=X_train['After_Lemmatization'].copy()
    pos_tagging(X_train,name='POS_tags')
    make_sentences(X_train,'POS_tags')
        



    """Εδώ προβαίνουμε σε μετασχηματισμό των δεδομένων μας σε διανυσματική μορφή. Αναγκαίο στάδιο αυτό για να μπορέσει να εκπαιδευτεί το μοντέλο μας,
    καθώς δεν είναι σε θέση να επεξεργαστεί παρά μόνο αριθμητικά δεδομένα. Χρησιμοποιούμε για το μετασχηματισμό αυτό τον TfidfVectorizer, ο οποίος μετράει
    τη σημαντικότητα λέξεων, λημμάτων, φράσεων στο πλαίσιο του corpus, στο οποίο περιλαμβάνεται. Αυτή η πληροφορία αποθηκεύεται σε μορφή διανύσματος. 
    Ο συγκεκριμένος vectorizer έχει ρυθμιστεί να παράγει unigrams, bigrams, trigrams και να μας επιστρέφει τα 5000 πιο σημαντικά unigrams,bigrams,trigrams."""

    tf_idf= TfidfVectorizer(lowercase=True, tokenizer=word_tokenize, ngram_range=(1,3), max_features=5000)

    X_text_tfidf= tf_idf.fit_transform(X_train['text'])
    X_text_tfidf = pd.DataFrame.sparse.from_spmatrix(X_text_tfidf)
    X_lemma_tfidf= tf_idf.fit_transform(X_train['After_Lemmatization'])
    X_lemma_tfidf= pd.DataFrame.sparse.from_spmatrix(X_lemma_tfidf)
    X_pos_tfidf= tf_idf.fit_transform(X_train['POS_tags'])
    X_pos_tfidf= pd.DataFrame.sparse.from_spmatrix(X_pos_tfidf)

    """συνενώνουμε τα εξαγόμενα από το vectorizer, ώστε να τα τροφοδοτήσουμε στο μοντέλο μας ως features πάνω στα οποία θα εκπαιδευτεί"""
    X = pd.concat([X_text_tfidf, X_lemma_tfidf, X_pos_tfidf], axis=1, join='inner')
    X_new = X.to_numpy()   
    



    """εδώ εκπαιδεύουμε το μοντέλο μας για τα polarities των προτάσεων. Αρχικά, προβαίνουμε σε feature selection αξιοποιώντας μόνο τα 1200 πιο σημαντικά 
    features από όλα εκείνα που μας έδωσε ο vectorizer."""
    X_new_pol = SelectKBest(chi2, k=1200).fit_transform(X_new, y['polarity'])   
    model_pol = svm.SVC(kernel='rbf')
    train_vectors_pol = model_pol.fit(X_new_pol,y['polarity'])
      
    """ Ακολουθούμε την ίδια διαδικασία και για την εκπαίδευση στα aspects. Και πάλι το ίδιο feature selection με παραπάνω"""
    X_new_asp = SelectKBest(chi2, k=1200).fit_transform(X_new, y['category'])
    model_asp = svm.SVC(kernel='rbf')
    train_vectors_asp = model_asp.fit(X_new_asp,y['category'])

      

    """Αποθηκεύουμε τα μοντέλο που έχουν εκπαιδευτεί για την πρόβλεψη τιμών polarities και aspect αντίστοιχα. Θα τα χρησιμοποιήσουμε στην επόμενη συνάρτηση"""
    # Save model to disk
    pickle.dump(train_vectors_pol, open('model_polarity', 'wb'))
    pickle.dump(train_vectors_asp, open('model_aspect', 'wb'))

    return None