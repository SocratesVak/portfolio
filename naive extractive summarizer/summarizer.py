
import nltk
nltk.download('stopwords')
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import heapq


filename='./articles/article10.txt'
file = open(filename, 'r',encoding= "utf-8")
content = file.read()


stop_words_set = set(stopwords.words('english'))


def split_to_sentences(content):
  sentences =[]
  sentences = sent_tokenize(content)
  for sentence in sentences:
    sentence.replace("[^a-zA-Z0-9]"," ")
  return sentences


def word_freq():
  sentences=split_to_sentences(content)
  tokens=[]
  for sent in sentences:
    tokens+=word_tokenize(sent)
  words=[word for word in tokens if word.isalnum()]

  word_freq = dict()
  for word in words:
    word.lower()
    if word not in stop_words_set:
      if word not in word_freq.keys():
        word_freq[word]=1
      else:
        word_freq[word]+=1
  return word_freq


def word_freq_per_sent():
  sentences=split_to_sentences(content)
  word_frequencies=word_freq()
  word_freq_per_sent=dict()
  for sentence in sentences:
    for word in word_tokenize(sentence):
      if word in word_frequencies.keys():
        if sentence not in word_freq_per_sent.keys():
          word_freq_per_sent[sentence]=word_frequencies[word]
        else:
          word_freq_per_sent[sentence]+=word_frequencies[word]
  return word_freq_per_sent


def sentences_weights():
  sentences=split_to_sentences(content)
  word_frequencies= word_freq()
  sentences_weights=dict()
  for sent in sentences:
    for word,freq in word_frequencies.items():
      if word in sent:
        if sent in sentences_weights.keys():
          sentences_weights[sent]+=freq
        else:
          sentences_weights[sent]=freq
  return sentences_weights


def summary():
  sentence_weights=sentences_weights()
  summary_sentences = heapq.nlargest(int((len(sentence_weights.keys()))/5), sentence_weights, key=sentence_weights.get)
  summary = ' '.join(summary_sentences)
  return summary


with open('article10_summary.txt',"w",encoding="utf-8") as f:
  f.write("Οι συχνότητες λέξεων του κειμένου είναι οι εξής: \n\n")
  f.write(str(word_freq()))
  f.write("\n\n\nΤο άθροισμα των συχνοτήτων λέξεων ανά πρόταση είναι το εξής:\n\n ")
  f.write(str(word_freq_per_sent()))
  f.write("\n\n\nΟι προτάσεις με την υψηλότερη βαθμολογία είναι οι εξής: \n\n")
  f.write(summary())



