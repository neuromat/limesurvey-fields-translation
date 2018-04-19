# Este script gera uma planilha com todos os códigos de questões, subquestões e
# respostas para facilitar a tradução.
#
# Entrada: Arquivo de estrutura de questionário "Ficha de Entrada" do
# LimeSurvey (limesurvey_survey_256242.lss)
#
# Saída: planilha com códigos para tradução

import csv
import nltk
import re
import xml.etree.ElementTree as ET

from nltk.corpus import stopwords


def strip_html(data):
    """
    remove html tag from data
    :param data: input string
    :return: input string whithout html tags
    """
    p = re.compile(r'<.*?>')
    return p.sub('', data)


def clean_field(content, size, prefix=''):
    clean_content = content

    # remove (s)
    clean_content = clean_content.replace('(s)', '')
    clean_content = clean_content.replace('(S)', '')

    words_to_exclude = stopwords.words('english')
    words_to_exclude.remove('other')
    words_to_exclude.remove('not')

    # remove stop words
    clean_content = ' '.join(
        [word for word in clean_content.split(' ')
         if word.lower() not in words_to_exclude]
    )

    # if there is a word in capital letter, ignore other words
    # TODO: select capital words only if it is word
    capital_words = \
        [word for word in re.sub("[^\w]", " ",  clean_content).split()
         if word.isupper() and len(word) > 2]
    if capital_words:
        clean_content = ' '.join(capital_words)

    # camel case
    clean_content = ''.join(
        x for x in clean_content.title() if not x.isspace()
    )

    # remove html tags
    clean_content = strip_html(clean_content)

    # remove special chars
    clean_content = ''.join(e for e in clean_content if e.isalnum())

    return (prefix + clean_content)[:size]


# load stopwords
nltk.download('stopwords')

question_types = {
    ';': ['Array (Flexible Labels) multiple texts', 'txt'],
    '*': ['Formula', 'equ'],
    '1': ['Array Dual Scale', 'lst'],
    'D': ['Date', 'dat'],
    'F': ['Array (Flexible Labels)', 'lst'],
    'H': ['Array (Flexible Labels) by Column', 'lst'],
    'L': ['List (Radio)', 'lst'],
    'M': ['Multiple choice', 'mul'],
    'N': ['Numerical Input', 'int'],
    'P': ['Multiple choice with comments', 'mul'],
    'T': ['Long Free Text', 'txt'],
    'X': ['Boilerplate Question', 'txt']
}

# known answer code translations
answer_code_translation_list = {
    'D': 'R',
    'E': 'L',
    'DE': 'RL',
    'NINA': 'NINA',
    'S': 'Y',
    'N': 'N',
    'nina': 'NINA',
    'Outra': 'Other'
}

# questions that should not be translated
special_question_codes = ['responsibleid', 'acquisitiondate', 'subjectid']

# input file: lss file (xml file)
# output file: csv file

# input_lss_file_name = \
#     '/Users/caco/Workspace/fields_translation/fields_translation/input' \
#     '/limesurvey_survey_256242.lss'
# output_csv_file_name = \
#     '/Users/caco/Workspace/fields_translation/fields_translation/output' \
#     '/spreadsheet_to_review_256242.csv'

# input_lss_file_name = \
#     '/Users/caco/Workspace/fields_translation/fields_translation/input/' \
#     'limesurvey_survey_593324.lss'
# output_csv_file_name = \
#     '/Users/caco/Workspace/fields_translation/fields_translation/output/' \
#     'spreadsheet_to_review_593324.csv'

input_lss_file_name = \
    '/Users/caco/Workspace/fields_translation/fields_translation/input' \
    '/limesurvey_survey_969322.lss'
output_csv_file_name = \
    '/Users/caco/Workspace/fields_translation/fields_translation/output' \
    '/spreadsheet_to_review_969322.csv'

groups = {}
answers = {}

tree = ET.parse(input_lss_file_name)

# navigate in "groups" elements
for item in tree.iterfind('groups/rows/row'):

    # fields to read:
    #   gid
    #   language
    #   group_name (depends of the language)
    #   group_order

    gid = item.findtext('gid')
    language = item.findtext('language')

    if gid not in groups:
        groups[gid] = {
            'gid': gid,
            'group_name': {},
            'order': item.findtext('group_order'),
            'questions': {}
        }

    groups[gid]['group_name'][language] = item.findtext('group_name')

# navigate in "questions" elements
for item in tree.iterfind('questions/rows/row'):

    # fields to read:
    #   gid
    #   qid
    #   language
    #   question_order
    #   type
    #   title (question_code)
    #   question (description, depends of the language)

    gid = item.findtext('gid')
    qid = item.findtext('qid')
    language = item.findtext('language')

    group = groups[gid]

    if qid not in group['questions']:
        groups[gid]['questions'][qid] = {
            'qid': qid,
            'order': int(item.findtext('question_order')),
            'type': item.findtext('type'),
            'question_code': item.findtext('title'),
            'description': {},
            'subquestions': {}
        }

    group['questions'][qid]['description'][language] = item.findtext('question')

# navigate in "subquestions" elements
for item in tree.iterfind('subquestions/rows/row'):

    # fields to read:
    #   gid
    #   language
    #   qid (subquestion id)
    #   parent_qid (question id)
    #   type (corresponde ao tipo da pergunta ou da subpergunta)
    #   title (subquestion_code)
    #   question (description, depends of the language)
    #   question_order

    gid = item.findtext('gid')
    subquestion_id = item.findtext('qid')
    language = item.findtext('language')
    question_id = item.findtext('parent_qid')

    question = groups[gid]['questions'][question_id]

    if subquestion_id not in question['subquestions']:
        question['subquestions'][subquestion_id] = {
            'subquestion_id': subquestion_id,
            'order': item.findtext('question_order'),
            'subquestion_code': item.findtext('title'),
            'type': item.findtext('type'),
            'description': {}
        }

    question['subquestions'][subquestion_id]['description'][language] = item.findtext('question')

# navigate in "answers" elements
for item in tree.iterfind('answers/rows/row'):
    # fields to read:
    #   qid (subquestion id)
    #   language
    #   code (answer code)
    #   scale_id (scale id, when question type is 'Array Dual Scale')
    #   answer (description, depends of the language)
    #   sortorder

    qid = item.findtext('qid')
    language = item.findtext('language')
    answer_code = item.findtext('code')
    scale = item.findtext('scale_id')

    if qid not in answers:
        answers[qid] = {
            'qid': qid,
            'answers': {}
        }

    subquestion = answers[qid]

    if answer_code not in subquestion['answers']:
        subquestion['answers'][answer_code] = {
            'answer_code': answer_code,
            'order': item.findtext('sortorder'),
            'scale': scale,
            'description': {}
        }

    subquestion['answers'][answer_code]['description'][language] = item.findtext('answer')

# generate csv file.
# Fields:
#     group
#     question_id
#     question_type
#     item
#     current question code
#     translated question code
#     current subquestion code
#     translated subquestion code
#     current answer code
#     translated answer code
#     description in portuguese
#     description in english

rows_to_be_saved = [
    ["group", "question_id", "question_type", "Item",
     "current question code", "translated question code",
     "current subquestion code", "translated subquestion code",
     "current answer code", "translated answer code",
     "description in portuguese", "description in english"]
]

translated_question_codes_list = {}
untranslated_answer_code_list = []

for group_item in sorted(groups.items(), key=lambda t: t[1]['order']):
    group = group_item[1]

    for question_item in sorted(group['questions'].items(), key=lambda t: t[1]['order']):
        question = question_item[1]

        translated_question_code = ""
        if question['question_code'] in special_question_codes:
            translated_question_code = question['question_code']
        else:
            if question['type'] == '*':
                # formula

                if question['question_code'][:4] == "form":
                    translated_question_code = question_types['*'][1] + question['question_code'][4:]
                else:
                    translated_question_code = question['question_code']
            elif question['type'] == 'X':
                # boilerplate question

                if question['question_code'][:3] == "tex":
                    translated_question_code = question_types['X'][1] + question['question_code'][3:]
                else:
                    translated_question_code = question['question_code']
            else:
                translated_question_code = clean_field(
                    question['description']['en'], 20,
                    question_types[question['type']][1]
                )

        while True:
            if translated_question_code not in translated_question_codes_list:
                translated_question_codes_list[translated_question_code] = 1
                break
            else:
                print("%s jah existente" % translated_question_code)  # DEBUG
                count = \
                    translated_question_codes_list[translated_question_code] \
                    + 1
                translated_question_codes_list[translated_question_code] = \
                    count
                translated_question_code = \
                    translated_question_code[:-1 * len(str(count))] + \
                    str(count)
                print("%s gerado..." % translated_question_code)  # DEBUG

        rows_to_be_saved.append([
            group['group_name']['pt-BR'],
            question['qid'],
            question['type'] + ' - ' + question_types[question['type']][0],
            'question',
            question['question_code'],
            translated_question_code,
            '',
            '',
            '',
            '',
            question['description']['pt-BR'],
            question['description']['en']
        ])

        translated_subquestion_codes_list = {}

        for subquestion_item in sorted(question['subquestions'].items(), key=lambda t: t[1]['order']):
            subquestion = subquestion_item[1]

            # print('        %s' % subquestion['description']['pt-BR'])

            if subquestion['subquestion_code'] == "NINA":
                translated_subquestion_code = "NINA"
            else:
                translated_subquestion_code = clean_field(subquestion['description']['en'], 20)

            if not translated_subquestion_code:
                print("subquestion %s da question %s ficou sem traducao" % (subquestion['subquestion_code'], question['question_code']))
                translated_subquestion_code = subquestion['subquestion_code']

            if translated_subquestion_code not in translated_subquestion_codes_list:
                translated_subquestion_codes_list[translated_subquestion_code] = 1
            else:
                print("%s jah existente" % translated_subquestion_code)  #
                # DEBUG
                count = translated_subquestion_codes_list[translated_subquestion_code] + 1
                translated_subquestion_codes_list[translated_subquestion_code] = count
                translated_subquestion_code = \
                    translated_subquestion_code[:-1 * len(str(count))] + \
                    str(count)
                print("%s gerado..." % translated_subquestion_code)  # DEBUG

            rows_to_be_saved.append([
                group['group_name']['pt-BR'],
                subquestion['subquestion_id'],
                question['type'] + ' - ' + question_types[question['type']][0],
                'subquestion',
                '',
                '',
                subquestion['subquestion_code'],
                translated_subquestion_code,
                # '',
                '',
                '',
                subquestion['description']['pt-BR'],
                subquestion['description']['en']
            ])

        if question['qid'] in answers:
            question_answers = answers[question['qid']]

            for answer_item in sorted(question_answers['answers'].items(), key=lambda t: t[1]['order']):
                answer = answer_item[1]
                # print('            %s' % answer['description']['pt-BR'])

                translated_answer_code = ""
                if answer['answer_code'] in answer_code_translation_list:
                    translated_answer_code = answer_code_translation_list[answer['answer_code']]
                else:
                    translated_answer_code = answer['answer_code']
                    untranslated_answer_code_list.append(answer['answer_code'])

                rows_to_be_saved.append([
                    group['group_name']['pt-BR'],
                    question['qid'],
                    question['type'] + ' - ' + question_types[question['type']][0],
                    'answer',
                    '',
                    '',
                    '',
                    '',
                    answer['answer_code'],
                    translated_answer_code,
                    answer['description']['pt-BR'],
                    answer['description']['en']
                ])

# Códigos de resposta não traduzidos
if untranslated_answer_code_list:
    print('Untranslated answer codes - begin')

    for item in untranslated_answer_code_list:
        print("\t %s" % item)

    print('Untranslated answer codes - end')

# Generating csv output file
with open(output_csv_file_name.encode('utf-8'), 'w', newline='', encoding='UTF-8') as csv_file:
    export_writer = csv.writer(csv_file, quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
    for row in rows_to_be_saved:
        export_writer.writerow(row)

print("\n --> The end")
