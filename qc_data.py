# -*- coding: utf-8 -*-
"""
Created on Wed Feb  6 18:51:49 2019

@author: swinchurkar
"""
import numpy as np
np.set_printoptions(threshold=np.inf)
import re
from matplotlib import pyplot
import itertools
import os
from collections import Counter

class Dataset():
    def __init__(self, training_dataset, test_dataset):
        self.training_dataset = training_dataset
        self.test_dataset = test_dataset
        self.y_classes = dict()
        self.y_classes_inv = dict()
        self.vocabulary = None
        self.vocabulary_inv = None


    def clean_text(self, text):
        ## Clean the text
        text = re.sub(r"[^A-Za-z0-9:(),!?\'\`]", " ", text)
        text = re.sub(r"what's", "what is ", text)
        text = re.sub(r"who's", "who is ", text)
        text = re.sub(r"how's", "how is ", text)
        text = re.sub(r"\'s", " ", text)
        text = re.sub(r"\'ve", " have ", text)
        text = re.sub(r"n't", " not ", text)
        text = re.sub(r"i'm", "i am ", text)
        text = re.sub(r"\'re", " are ", text)
        text = re.sub(r"\'d", " would ", text)
        text = re.sub(r"\'ll", " will ", text)
        text = re.sub(r",", " ", text)
        text = re.sub(r"\.", " ", text)
        text = re.sub(r"!", " ! ", text)
        text = re.sub(r"\/", " ", text)
        text = re.sub(r"\^", " ^ ", text)
        text = re.sub(r"\+", " + ", text)
        text = re.sub(r"\-", " - ", text)
        text = re.sub(r"\=", " = ", text)
        text = re.sub(r"'", " ", text)
        text = re.sub(r"(\d+)(k)", r"\g<1>000", text)
        text = re.sub(r" e g ", " eg ", text)
        text = re.sub(r" b g ", " bg ", text)
        text = re.sub(r" u s ", " american ", text)
        text = re.sub(r"\0s", "0", text)
        text = re.sub(r" 9 11 ", "911", text)
        text = re.sub(r"e - mail", "email", text)
        text = re.sub(r"j k", "jk", text)
        text = re.sub(r"\s{2,}", " ", text)
        text = re.sub(r" : ", ":", text)
        text = re.sub(r",", " , ", text)
        text = re.sub(r"!", " ! ", text)
        text = re.sub(r"\(", " \( ", text)
        text = re.sub(r"\)", " \) ", text)
        text = re.sub(r"\?", " \? ", text)
        text = re.sub(r"\s{2,}", " ", text)      
        return text.strip().lower()
      
    def pad_sentences(self, sentences, padding_word="<PAD/>"):
        sequence_length = max(len(x) for x in sentences)
        padded_sentences = []
        for i in range(len(sentences)):
            sentence = sentences[i]
            num_padding = sequence_length - len(sentence)
            new_sentence = sentence + [padding_word] * num_padding
            padded_sentences.append(new_sentence)
        return padded_sentences

    def build_vocab(self, sentences):
        print("Building vocabulary")
        # Build vocabulary
        word_counts = Counter(itertools.chain(*sentences))
        # Mapping from index to word
        # vocabulary_inv=['<PAD/>', 'the', ....]
        self.vocabulary_inv = [x[0] for x in word_counts.most_common()]
        # Mapping from word to index
        # vocabulary = {'<PAD/>': 0, 'the': 1, ',': 2, 'a': 3, 'and': 4, ..}
        self.vocabulary = {x: i for i, x in enumerate(self.vocabulary_inv)}

    def fit_on_texts(self, sentences, labels):
        print("Converting text to sequences")
        x = np.array([[self.vocabulary[word] for word in sentence] for sentence in sentences])
        y = np.array(labels)
        return [x, y]

    def load(self, val_split):
        print("Loading data")
        x_train_data = list(open(self.training_dataset, encoding = 'utf-8').readlines())
        x_test_data = list(open(self.test_dataset, encoding = 'utf-8').readlines())
        test_size = len(x_test_data)
        
        x_text_data = x_train_data + x_test_data
        x_text_data = [self.clean_text(sent) for sent in x_text_data]
        y_text_data = [s.split(' ')[0].split(':')[0] for s in x_text_data]
        x_text_data = [s.split(" ")[1:] for s in x_text_data]
                             
        for label in y_text_data:
            if not label in self.y_classes_inv:
                indx = len(self.y_classes_inv)
                self.y_classes_inv[label] = indx
                self.y_classes[indx] = label
        
        one_hot = np.identity(len(self.y_classes_inv))
        y_labels = [one_hot[ self.y_classes_inv[label]-1 ] for label in y_text_data]
    
        x_text_data = self.pad_sentences(x_text_data)
        self.build_vocab(x_text_data)
        self.x_test_text = x_text_data[-test_size:]
        self.y_test_text = y_text_data[-test_size:]
        x, y = self.fit_on_texts(x_text_data, y_labels)
        
        x_train_, x_test = x[:-test_size], x[-test_size:]
        y_train_, y_test = y[:-test_size], y[-test_size:]
        shuffle_indices = np.random.permutation(np.arange(len(y_train_)))
        x_shuffled = x_train_[shuffle_indices]
        y_shuffled = y_train_[shuffle_indices]
                
        # Split train/hold-out/test set
        x_train, x_val = x_shuffled[:-val_split], x_shuffled[-val_split:]
        y_train, y_val = y_shuffled[:-val_split], y_shuffled[-val_split:]
        
        return [x_train, y_train, x_val, y_val, x_test, y_test]
    
    def print_training_stat(self, logs_dir, color_list):
        # Read a data file
        class_stat = np.zeros(self.get_num_class())
        texts = []
        line_no = 0
        file = open(self.training_dataset, "r", encoding = 'utf-8')
        for line in file:
            texts += [line]
            words = line.split(":")
            class_stat[self.y_classes_inv[words[0].lower()]] += 1    
            line_no += 1
        file.close()
        
        print("Training Dataset:")
        class_index = []
        class_stat_per = np.zeros(self.get_num_class())
        for indx in range(self.get_num_class()):
            class_stat_per[indx] = (class_stat[indx] / line_no) * 100
            class_index.append(self.y_classes[indx].upper())
            print("Class : ", indx, "\t: ", self.y_classes[indx].upper(), " = ", class_stat[indx], "\t: % ", round(class_stat_per[indx], 1))
              
        print("Questions in training dataset: ", line_no)
        
        class_fig = pyplot.figure()
        pyplot.bar(class_index, class_stat_per,  
        width = 1.0, color = color_list) 
        pyplot.xlabel('Question Type Class', fontsize=18) 
        pyplot.ylabel('Distribution (%)', fontsize=18) 
        pyplot.title('Question Type Training Data Distribution Graph', fontsize=18)
        filename = os.path.join(logs_dir, "qtype_train_data_distribution.png")
        class_fig.savefig(filename)
        pyplot.show()
    
    def print_test_stat(self, logs_dir, color_list):
        # Read a data file
        class_stat = np.zeros(self.get_num_class())
        texts = []
        line_no = 0
        file = open(self.test_dataset, "r", encoding = 'utf-8')
        for line in file:
            texts += [line]
            words = line.split(":")
            #if line_no != 0:
            class_stat[self.y_classes_inv[words[0].lower()]] += 1    
            line_no += 1
        file.close()
        
        print("Test Dataset:")
        class_index = []
        class_stat_per = np.zeros(self.get_num_class())
        for indx in range(self.get_num_class()):
            class_stat_per[indx] = (class_stat[indx] / line_no) * 100
            class_index.append(self.y_classes[indx].upper())
            print("Class : ", indx, "\t: ", self.y_classes[indx].upper(), " = ", class_stat[indx], "\t: % ", round(class_stat_per[indx], 1))
              
        print("Questions in test dataset: ", line_no)    
        class_fig = pyplot.figure()
        pyplot.bar(class_index, class_stat_per,  
        width = 1.0, color = color_list) 
        pyplot.xlabel('Question Type Class', fontsize=18) 
        pyplot.ylabel('Distribution (%)', fontsize=18) 
        pyplot.title('Question Type Test Data Distribution Graph', fontsize=18)
        filename = os.path.join(logs_dir, "qtype_test_data_distribution.png")
        class_fig.savefig(filename)
        pyplot.show()
        
    def print_stat(self, logs_dir):    
        color_list = ['red', 'green', 'blue', 'orange', 'yellow', 'black']
        
        #cmap = pyplot.get_cmap(1)
        #cmap = pyplot.get_cmap('brg')
        #for i in range(self.get_num_class()):
        #    color_list.append(cmap(i))
        
        print("color_list : ", color_list)        
        print("Words in Vocabulary: ", self.get_voc_size())
        print("Classes: ", self.get_num_class())
                    
        self.print_training_stat(logs_dir, color_list)
        self.print_test_stat(logs_dir, color_list)
       
    def write_predections(self, filename, y_test, y_pred):
        texts = "PREDICTED,ACTUAL,QUESTION\n"
        target = []
        indx = 0
        for line in self.x_test_text:
            target.append(self.y_classes[y_pred[indx]].upper())
            target.append(self.y_classes[y_test[indx]].upper())
            target.append(' '.join(line))
            text = ','.join(str(e) for e in target)
            texts += text + '\n'
            target = []
            indx += 1
                
        file = open(filename, "w", encoding = 'utf-8')
        file.write(texts)
        file.close()


    def get_num_class(self):
        return len(self.y_classes)

    def get_class_labels(self):
        return self.y_classes
        
    def get_voc_size(self):
        return len(self.vocabulary_inv)
        
    def batch_iter(self, data, batch_size, num_epochs):
        data = np.array(data)
        data_size = len(data)
        num_batches_per_epoch = int(len(data)/batch_size) + 1
        for epoch in range(num_epochs):
            # Shuffle the data at each epoch
            shuffle_indices = np.random.permutation(np.arange(data_size))
            shuffled_data = data[shuffle_indices]
            for batch_num in range(num_batches_per_epoch):
                start_index = batch_num * batch_size
                end_index = (batch_num + 1) * batch_size
                if end_index > data_size:
            	    end_index = data_size
            	    start_index = end_index - batch_size
                yield shuffled_data[start_index:end_index]