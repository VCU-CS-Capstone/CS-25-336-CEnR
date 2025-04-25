from flask import Flask, flash, request, redirect, url_for, render_template
from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
import os
from pathlib import Path
import tarfile
import zipfile
import pandas as pd
import string
import re
from simpletransformers.classification import ClassificationModel
import json

import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer, WordNetLemmatizer


UPLOAD_FOLDER = 'uploads'
REFERENCE_FOLDER = 'reference files'
ALLOWED_EXTENSIONS = {}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['REFERENCE_FOLDER'] = REFERENCE_FOLDER
app.config['SECRET_KEY'] = "thiskeyisnotsecret"

datafiles = []
merged_distribution_files = []
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
    model_dir = os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'], 'models')  # define model_dir
    metadata_path = os.path.join(model_dir, 'model_info.json')

    model_descriptions = {}

    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            model_descriptions = json.load(f)

    return model_descriptions

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

        self.process()

compatible_data_filetypes = {'xls', 'xlsx', 'xlsm', 'xlsb', 'odf', 'ods', 'odt'}
compatible_model_compressions = {}

@app.route("/", methods= ['GET', 'POST'])
@app.route("/index", methods= ['GET', 'POST'])
def main_page():
    run_form = RunForm()
    run_form.updateForm()
    model_descr = get_descr()
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
                datafile.save(os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'], 'datafiles', datafile_name))
                read_files()
        elif(request.form['form_name'] == "upload-model"):
            modelfile = request.files['modelfile']
            if(modelfile and (modelfile.filename.rsplit('.', 1)[1].lower() in compatible_model_compressions)):
                modelfile_name = secure_filename(modelfile.filename)
                modelfile.save(os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'], 'models', modelfile_name))
                read_files()

    run_form.updateForm()
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
    references_folder = os.path.join(os.getcwd(), app.config['REFERENCE_FOLDER'])
    references_file = os.path.join(os.getcwd(), app.config['REFERENCE_FOLDER'], os.listdir(references_folder)[0])
    reference = pd.read_excel(references_file).rename(columns={"IRB Protocol": "IRB_ID"})

    global datafiles
    global merged_distribution_files
    global modelfiles
    for file in os.listdir(f"{uploads_folder}/datafiles"):
        filepath = os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'], 'datafiles', file)
        if file.endswith(('xls', 'xlsx', 'xlsm', 'xlsb', 'odf', 'ods', 'odt')):
            num_lines = len(pd.read_excel(filepath))
        
        # JSON not well-represented in sample data; only two json files exist, and both are missing headers which are critical for data search in this process
        # Therefore json compatibility was not a priority
        # It's currently recommended to convert a json file into a properly-formatted excel file instead, which ensures proper processing
        #elif file.endswith(('json')):
        #    num_lines = len(pd.read_json(filepath, typ='frame'))

        datafile_object = ((filepath, Path(filepath).stem, Path(filepath).suffix, num_lines))
        if(datafile_object in datafiles): break     # If this file has already been processed, skip it
            
        datafiles.append(datafile_object)

        df = pd.read_excel(filepath)
        if('DateApproved' in df.columns):
            df = df.dropna(subset=['DateApproved'])
        
        if('ID' in df.columns): 
            df = df.rename(columns={"ID": "IRB_ID"})
        elif('ProtocolNum' in df.columns): df = df.rename(columns={"ProtocolNum": "IRB_ID"})
        elif('Protocol ID' in df.columns): df = df.rename(columns={"Protocol ID": "IRB_ID"})
        elif('IRB Protocol' in df.columns): df = df.rename(columns={"IRB Protocol": "IRB_ID"})
        elif('BaseProtocolNum' in df.columns): df = df.rename(columns={"BaseProtocolNum": "IRB_ID"})
        else: break # Prevents an exception if the excel file isn't properly formatted with an acceptable IRB ID field
        df = df.drop_duplicates(subset="IRB_ID")

        distribution_df = pd.merge(df, reference, on="IRB_ID", how='left')
        distribution_df_only_non_null = pd.merge(df, reference, on="IRB_ID", how='inner')

        merged_distribution_files.append((distribution_df, len(distribution_df), distribution_df_only_non_null, len(distribution_df_only_non_null)))

        print(len(distribution_df), len(distribution_df_only_non_null), len(distribution_df) - len(distribution_df_only_non_null))

        """id_aliases = ['ID', 'ProtocolNum', 'Protocol ID', 'IRB Protocol', 'BaseProtocolNum']
        IRB_id = df[[i for i in id_aliases if i in df.columns]]
        IRB_id = IRB_id.rename(index={0: "IRB_ID"}).iloc[:, 0]

        AimsGoals_aliases = ['AimsGoal', 'AimsGoals']
        aims_goals = df[[i for i in AimsGoals_aliases if i in df.columns]]
        aims_goals = aims_goals.rename(index={0: "Aims_Goals"}).iloc[:, 0]

        hypothesis = df['Hypothesis']

        background = df['Background']

        StudyDesign_aliases = ['Study Design', 'StudyDesign']
        study_design = df[[i for i in StudyDesign_aliases if i in df.columns]]
        study_design = study_design.rename(index={0: "Study_Design"}).iloc[:, 0]"""

    # Look for a packaged file which should contain a model
    # Only tarball and .zip formats are currently supported; support could be extended to ex. 7zip and gzip
    for file in os.listdir(f"{uploads_folder}"): 
        filepath = os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'], file)
        if os.path.isfile(filepath):
            if file.endswith(('tar', 'tgz', 'tbz', 'txz', 'tzst')):
                with tarfile.open(filepath, "r") as tar:
                    tar.extractall(f"{uploads_folder}/models")
            elif file.endswith(('zip')):
                with zipfile.ZipFile(filepath, "r") as zip:
                    zip.extractall(f"{uploads_folder}/models")


    for model_folder in os.listdir(f"{uploads_folder}/models"):
        break

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