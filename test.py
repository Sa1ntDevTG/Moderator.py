import sys
sys.path.append("./censure") # allow module import from git submodule

from censure import Censor

censor_ru = Censor.get(lang='ru')
censor_en = Censor.get(lang='en')
text = 'блять лол блять'
text = censor_ru.clean_line(text)

print(text[0])