:: Builds all the models for Norwegian NLP functionality and places them in the default locations

set PYTHONPATH=%PYTHONPATH%;%~dp0\..

mkdir %~dp0\..\..\models

python %~dp0\build_no_tagger.py -m %~dp0\..\..\models\nob-tagger-default-model --features simple --language nob
python %~dp0\build_no_tagger.py -m %~dp0\..\..\models\nno-tagger-default-model --features simple --language nno
