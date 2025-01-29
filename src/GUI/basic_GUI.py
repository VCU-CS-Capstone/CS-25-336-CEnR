from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import tarfile
import pandas as pd
import string
import re
from simpletransformers.classification import ClassificationModel

import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer, WordNetLemmatizer


UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = "thiskeyisnotsecret"

model_args = {
    'evaluate_during_training': False,
    'logging_steps': 10,
    'num_train_epochs': 3,
    'evaluate_during_training_steps': 500,
    'save_eval_checkpoints': False,
    'manual_seed':4,
    'train_batch_size': 32,
    'eval_batch_size': 8,
    'overwrite_output_dir': True,
    'learning_rate': 3e-5,
    'sliding_window':True,
    'max_seq_length':128,
    'use_cuda':False,
    'silent':True,
    'no_cache':True,
}

@app.route("/", methods = ['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        if 'zipfile' not in request.files:
            flash('No zip part')
            return redirect(request.url)
        if 'datafile' not in request.files:
            flash('No data part')
            return redirect(request.url)

        zipfile = request.files['zipfile']
        datafile = request.files['datafile']
        
        if zipfile.filename == '':
            flash('No zip file selected')
            return redirect(request.url)
        if datafile.filename == '':
            flash('No data file selected')
            return redirect(request.url)

        if (zipfile and (zipfile.filename.rsplit('.', 1)[1].lower() in {'tar'}) 
        and datafile and (datafile.filename.rsplit('.', 1)[1].lower() in {'xlsx'})):
            zipfile_name = secure_filename(zipfile.filename)
            datafile_name = secure_filename(datafile.filename)
            zipfile.save(os.path.join(app.config['UPLOAD_FOLDER'], zipfile_name))
            datafile.save(os.path.join(app.config['UPLOAD_FOLDER'], datafile_name))
            return redirect(url_for('display_output', zipname=zipfile_name, dataname=datafile_name))
    return '''
    <!doctype html>
    <title>Upload new Files</title>
    <h1>Upload model archive and data files</h1>
    <form method=post enctype=multipart/form-data>
        <h2>Upload tar file</h2>
        <input type=file name=zipfile>
        <h2>Upload xlsx file</h2>
        <input type=file name=datafile>
        <p></p>
        <input type=submit value=Upload>
    </form>
    '''

@app.route('/outputs/<zipname>+<dataname>')
def display_output(zipname, dataname):
    with tarfile.open(f"{UPLOAD_FOLDER}/{zipname}", "r") as tar:
        tar.extractall(f"{UPLOAD_FOLDER}")

    datafile_df = pd.read_excel(f"{UPLOAD_FOLDER}/{dataname}")
    datafile_df = datafile_df.fillna("")
    datafile_df['New'] = datafile_df['AimsGoal'] + datafile_df['Hypothesis'] + datafile_df['Background'] + datafile_df['Study Design']
    datafile_df['New'] = datafile_df['New'].astype(str)
    valtext = datafile_df['New'].map(lambda x: clean_text(x))
    bestcheckpoint_model = ClassificationModel("bert", f"{UPLOAD_FOLDER}/{zipname.rsplit('.', 1)[0]}", args=model_args, num_labels=3, use_cuda=False)
    predictions, raw_outputs = bestcheckpoint_model.predict(valtext)

    return '''
    <!doctype html>
    <title>Outputs</title>
    <h1>Output for selected files: %s, %s </h1>
    <p>%s</p>
    ''' % (zipname, dataname, predictions)


def clean_text(text):
    
    ## Remove puncuation
    text = text.translate(string.punctuation)
    
    ## Convert words to lower case and split them
    text = text.lower().split()
    
    ## Remove stop words
    #nltk.download('stopwords')
    stops = set(stopwords.words("english"))
    text = [w for w in text if not w in stops and len(w) >= 3]
    
    text = " ".join(text)
    ## Clean the text
    text = re.sub(r"[^A-Za-z0-9^,!.\/'+-=]", " ", text)
    text = re.sub(r"what's", "what is ", text)
    text = re.sub(r"\'s", " ", text)
    text = re.sub(r"\'ve", " have ", text)
    text = re.sub(r"n't", " not ", text)
    text = re.sub(r"i'm", "i am ", text)
    text = re.sub(r"\'re", " are ", text)
    text = re.sub(r"\'d", " would ", text)
    text = re.sub(r"\'ll", " will ", text)
    text = re.sub(r",", " ", text)
    text = re.sub(r"\.", " ", text)
    text = re.sub(r"!", "  ", text)
    text = re.sub(r"=", "  ", text)
    text = re.sub(r"\/", " ", text)
    text = re.sub(r"\^", " ^ ", text)
    text = re.sub(r"\+", " + ", text)
    text = re.sub(r"\-", " - ", text)
    text = re.sub(r"\=", " = ", text)
    text = re.sub(r"'", " ", text)
    text = re.sub(r"(\d+)(k)", r"\g<1>000", text)
    text = re.sub(r":", "  ", text)
    text = re.sub(r";", "  ", text)
    text = re.sub(r"http", "  ", text)
    text = re.sub(r"www", "  ", text)
    text = re.sub(r"-", "  ", text)
    text = re.sub(r" e g ", " eg ", text)
    text = re.sub(r" b g ", " bg ", text)
    text = re.sub(r"\0s", "0", text)
    text = re.sub(r" 9 11 ", "911", text)
    text = re.sub(r"e - mail", "email", text)
    text = re.sub(r"j k", "jk", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\d+", " ", text)

    ## Lemmatize
    text = text.split()
    lemmatizer = WordNetLemmatizer()
    lemma_words = [lemmatizer.lemmatize(word) for word in text]
    text = " ".join(lemma_words)

    return text