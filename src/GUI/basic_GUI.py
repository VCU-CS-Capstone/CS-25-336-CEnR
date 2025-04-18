from flask import Flask, flash, request, redirect, url_for, render_template
from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
import os
from pathlib import Path
import tarfile
import pandas as pd
import string
import re
from simpletransformers.classification import ClassificationModel

import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer, WordNetLemmatizer


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = "thiskeyisnotsecret"

datafiles = []
modelfiles = []
model_descr = {}

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

def get_descr():
    # Load description map if available
    metadata_path = os.path.join(model_dir, 'model_info.json')
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            model_descriptions = json.load(f)

class RunForm(FlaskForm):
    dataset = SelectField('Select Dataset', validators=[DataRequired()])
    model = SelectField('Select Model', validators=[DataRequired()])

    def updateForm(self):
        global datafiles
        global modelfiles
        dataset_choices = [(file, file[1]) for file in datafiles]
        self.dataset.choices = dataset_choices

        model_choices = [(file, file[1]) for file in modelfiles]
        self.model.choices = model_choices



        #self.process()

compatible_data_filetypes = {'xls', 'xlsx', 'xlsm', 'xlsb', 'odf', 'ods', 'odt'}
compatible_model_compressions = {}

@app.route("/", methods= ['GET', 'POST'])
@app.route("/index", methods= ['GET', 'POST'])
def main_page():
    run_form = RunForm()
    run_form.updateForm()
    if request.method == 'POST':
        if(request.form['form_name'] == "run-model"):
            if run_form.validate_on_submit():
                selected_dataset = run_form.dataset.data
                selected_model = run_form.model.data
                return f'You selected: {selected_dataset}, {selected_model}'
        elif(request.form['form_name'] == "upload-dataset"):
            datafile = request.files['datafile']
            if(datafile and (datafile.filename.rsplit('.', 1)[1].lower() in compatible_data_filetypes)):
                datafile_name = secure_filename(datafile.filename)
                datafile.save(os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'], datafile_name))
        elif(request.form['form_name'] == "upload-model"):
            modelfile = request.files['modelfile']
            if(modelfile and (modelfile.filename.rsplit('.', 1)[1].lower() in compatible_model_compressions)):
                modelfile_name = secure_filename(modelfile.filename)
                modelfile.save(os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'], modelfile_name))

    return render_template('CEnR_HTML.html', run_form=run_form, model_descr=model_descr)

'''
@app.route("/", methods = ['GET', 'POST'])
@app.route("/index", methods = ['GET', 'POST'])
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
    return render_template('CEnR_HTML.html')'''
'''
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

'''@app.route('/outputs/<zipname>+<dataname>')
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

    return
    <!doctype html>
    <title>Outputs</title>
    <h1>Output for selected files: %s, %s </h1>
    <p>%s</p>
     % (zipname, dataname, predictions)'''

def read_files():
    uploads_folder = os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'])
    global datafiles
    global modelfiles
    for file in os.listdir(uploads_folder):
        filepath = os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'], file)
        if file.endswith(('xls', 'xlsx', 'xlsm', 'xlsb', 'odf', 'ods', 'odt')):
            datafiles.append((filepath, Path(filepath).stem, Path(filepath).suffix, len(pd.read_excel(filepath))))

    return


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

if __name__ == '__main__':
    read_files()
    app.run(debug=True, port=5001)