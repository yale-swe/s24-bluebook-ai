# s24-bluebook-ai
To run frontend or backend code, please add an `.env` file inside that directory and put your API key in it, such as
```
OPENAI_API_KEY=sk-XXX
```
Don't push your API key to this repo!

To run sentiment classification, first create a conda environment for Python 3 using the requirements.txt file:
```
conda create --name <env_name> --file sent_classif_requirements.txt
```
Activate the conda environment by running:
```
conda activate <env_name>
```
where `<env_name>` is your name of choice for the conda environment.
