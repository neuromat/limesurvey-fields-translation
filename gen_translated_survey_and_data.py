#!/usr/bin/python3

"""
Generates new files to LimeSurvey with codes (questions, subquestions,
answers), translated
Entry: spreadsheet translated/reviewd, file with original questionnaire
structure, original data file
Outputs: data file with translated codes, questionnaire structure file with
translated codes

TODO:
Initial validations:
- check for any untranslated code
- check if any code contains whitespace or any special characters
- check if any code has exceeded the maximum allowed character size:
    question: limit = 20 characters
    subquestion: limit = 20 characters
    answer: limit = 5 characters
- check for any duplicate code
End validations:
- check for any of the questions/subquestions/answers throughout the text
- check if the questionnaire still works properly using it in NES
- list the translations equal to originals
Functional tests:
- check if files are imported properly in LimeSurvey
- check if it worked with the types of questions used
';': 'Array (Flexible Labels) multiple texts',
'*': 'Formula',
'1': 'Dual Scale Array'
'D': 'Date',
'F': 'Array (Flexible Labels)',
'H': 'Array (Flexible Labels) by Column',
'L': 'List (Radio)',
'M': 'Multiple choice'
'N': 'Numerical Input'
'P': 'Multiple choice with comments',
'T': 'Long Free Text',
'X': 'Boilerplate Question'
- check if formulas continue to work
"""

import csv
from xml.etree import ElementTree as ETree
from shutil import copyfile

# Arquivos de entrada

# input_lss_original_file_name = \
#     "/Users/caco/Workspace/fields_translation/fields_translation/input" \
#     "/limesurvey_survey_256242.lss"
# input_csv_original_file_name = \
#     "/Users/caco/Workspace/fields_translation/fields_translation/input" \
#     "/vvexport_256242.csv"
# input_csv_reviewed_spreadsheet = \
#     "/Users/caco/Workspace/fields_translation/fields_translation/output" \
#     "/spreadsheet_to_review_256242.csv"

# input_lss_original_file_name = \
#     "/Users/caco/Workspace/fields_translation/fields_translation/input" \
#     "/limesurvey_survey_593324.lss"
# input_csv_original_file_name = \
#     "/Users/caco/Workspace/fields_translation/fields_translation/input" \
#     "/vvexport_593324.csv"
# input_csv_reviewed_spreadsheet = \
#     "/Users/caco/Workspace/fields_translation/fields_translation/output" \
#     "/spreadsheet_to_review_593324.csv"

input_lss_original_file_name = \
    "/Users/caco/Workspace/fields_translation/fields_translation/input" \
    "/limesurvey_survey_969322.lss"
input_csv_original_file_name = \
    "/Users/caco/Workspace/fields_translation/fields_translation/input" \
    "/vvexport_969322.csv"
input_csv_reviewed_spreadsheet = \
    "/Users/caco/Workspace/fields_translation/fields_translation/output" \
    "/spreadsheet_to_review_969322.csv"

# read spreadsheet translated
with open(input_csv_reviewed_spreadsheet, 'r') as f:
    reader = csv.reader(f)
    spreadsheet_list = list(reader)

questions = {}
question_ids = {}

current_question = None

for index, line in enumerate(spreadsheet_list):
    # header in first line

    if index > 0:

        question_id = line[1]
        question_type = line[2]
        item = line[3]

        # new question
        if item == 'question':

            current_question_code = line[4]
            translated_question_code = line[5]

            current_question = current_question_code

            if current_question in questions:
                print("Não deveria haver questao com o mesmo código")
            else:
                question_ids[question_id] = current_question
                questions[current_question] = {
                    'translated_question_code': translated_question_code,
                    'question_id': question_id,
                    'question_type': question_type,
                    'subquestions': {},
                    'answers': {}}

        elif item == "subquestion":

            current_subquestion_code = line[6]
            translated_subquestion_code = line[7]

            if current_subquestion_code in questions[current_question]['subquestions']:
                print("Não deveria haver subquestao com mesmo código na questão")
            else:
                questions[current_question]['subquestions'][current_subquestion_code] = {
                    'translated_subquestion_code': translated_subquestion_code,
                    'subquestion_id': question_id}

        elif item == "answer":

            current_answer_code = line[8]
            translated_answer_code = line[9]

            if current_answer_code in questions[current_question]['answers']:
                print("Não deveria haver resposta com mesmo código na questão")
            else:
                questions[current_question]['answers'][current_answer_code] = \
                    {'translated_answer_code': translated_answer_code}

# Validações na planilha

# Abrir lss original e gerar cópia do lss a ser traduzido
file_name_part_list = input_lss_original_file_name.split('input')
file_name_part_list = file_name_part_list[0] + 'output' + \
                      file_name_part_list[1]
file_name_part_list = file_name_part_list.split('.')
output_new_lss_file_name = file_name_part_list[0] + "_new." + \
                            file_name_part_list[1]
# copyfile(input_lss_original_file_name, output_new_lss_file_name)
copyfile(input_lss_original_file_name, "temp_lss.lss")

tree = ETree.parse("temp_lss.lss")

for item in tree.iterfind('questions/rows/row'):
    # fields to read:
    #   gid
    #   qid
    #   language
    #   question_order
    #   type
    #   title (question_code)
    #   question (description, depends of the language)
    question_code = item.findtext('title')
    if question_code in questions:
        item.find('title').text = questions[question_code]['translated_question_code']

    # traducao de formulas e textos
    if item.findtext('type') in ("*", "X"):
        original_text = item.findtext('question')
        # print("")
        # print(original_text)
        for question in questions:
            if question in original_text:
                # print("-")
                # print(question)
                item.find('question').text = \
                    item.findtext('question').replace(question, questions[question]['translated_question_code'])

    # traducao do campo relevance (relacionado ao conditions)

    # Exemplos de relevance:
    #   (1) 1
    #   (2) ((256242X320X16516.NAOK == "S"))
    #   (3) ((256242X320X16517Outro.NAOK == "Y"))
    #   (4) ((256242X319X16495.NAOK == "D" or 256242X319X16495.NAOK == "DE"))
    #   (5) ((256242X322X17689Trofismo#1.NAOK == "P"))
    #
    #   *Exemplo (1): não há nada para fazer
    #   *Exemplo (2): questão 16516 não contém subquestion, temos que traduzir somente a resposta
    #   *Exemplo (3): questão 16517 contém subquestion, temos que traduzir a subquestion e a resposta
    #   Exemplo (4): podemos encontrar mais do que uma parte para traduzir
    #   *Exemplo (5): às vezes a subquestion vem com um sufixo '#'

    relevance = item.findtext('relevance')
    # print(relevance)
    current_pos = 0
    naok_pos = relevance.find('NAOK', current_pos)

    while naok_pos != -1:

        # traducao do subquestion

        pieces = relevance[current_pos:naok_pos].split('X', maxsplit=2)

        # ultima parte pode conter subquestion_code
        # print(pieces[-1])
        question_id = pieces[-1][:5]
        subquestion_code = pieces[-1][5:].split('.')[0].split('#')[0]

        # if subquestion_code:
        #     print('%s - %s' % (pieces[-1], pieces[-1][5:].split('.')[0].split('#')[0]))

        if question_id in question_ids:
            question_code = question_ids[question_id]

            if question_code in questions:

                if questions[question_code]['subquestions']:

                    # print("")
                    # print(relevance)
                    # print('%s - %s - %s' % (pieces[-1], subquestion_code, questions[question_code]['subquestions'][subquestion_code]['translated_subquestion_code']))
                    pieces[-1] = pieces[-1].replace(subquestion_code, questions[question_code]['subquestions'][subquestion_code]['translated_subquestion_code'])
                    # print(pieces[-1])

                    relevance = relevance[:current_pos] + 'X'.join(pieces) + relevance[naok_pos:]
                    item.find('relevance').text = relevance
                    naok_pos = relevance.find('NAOK', current_pos)

        # traducao do answer
        if question_id in question_ids:
            question_code = question_ids[question_id]
            if question_code in questions:

                pieces = relevance[naok_pos + 9:].split('"')
                # print("%s" % (pieces[0]))
                answer_code = pieces[0]

                if 'answers' in questions[question_code]:
                    if answer_code in questions[question_code]['answers']:
                        pieces[0] = questions[question_code]['answers'][answer_code]['translated_answer_code']
                        relevance = relevance[:naok_pos + 9] + '"'.join(pieces)
                        # print("-> %s" % pieces[0])
                        # print("  --> %s" % relevance)
                        item.find('relevance').text = relevance
                        naok_pos = relevance.find('NAOK', current_pos)

                    # else:
                    #     print("deveria existir answer %s para a question %s" % (answer_code, question_code))
                else:
                    print("question %s nao contem answers")

        # proximo 'NAOK'
        current_pos = naok_pos + 1
        naok_pos = relevance.find('NAOK', current_pos)

    # procurar NAOK até nao encontrar mais
    # buscar X a

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

    question_id = item.findtext('parent_qid')

    if question_id in question_ids:

        question_code = question_ids[question_id]
        subquestion_code = item.findtext('title')

        if subquestion_code in questions[question_code]['subquestions']:
            item.find('title').text = questions[question_code]['subquestions'][subquestion_code]['translated_subquestion_code']

for item in tree.iterfind('answers/rows/row'):
    # fields to read:
    #   qid (question id)
    #   code (answer code)

    question_id = item.findtext('qid')

    if question_id in question_ids:

        question_code = question_ids[question_id]
        answer_code = item.findtext('code')

        if answer_code in questions[question_code]['answers']:
            item.find('code').text = questions[question_code]['answers'][answer_code]['translated_answer_code']

for item in tree.iterfind('conditions/rows/row'):
    question_id = item.findtext('cqid')
    if question_id in question_ids:
        question_code = question_ids[question_id]
        # translate subquestion
        if questions[question_code]['subquestions']:
            field_name = item.findtext('cfieldname')
            fields = field_name.split('X', maxsplit=2)
            pieces = fields[-1].split('#')
            subquestion_code = pieces[0].replace(questions[question_code]['question_id'], '')
            if subquestion_code in questions[question_code]['subquestions']:
                item.find('cfieldname').text = \
                    'X'.join(fields[:-1] +
                             ['#'.join([questions[question_code]['question_id']
                                        + questions[question_code]
                                        ['subquestions'][subquestion_code]
                                        ['translated_subquestion_code']]
                                       + pieces[1:])])
            else:
                print("Subquestion %s deveria existir" % subquestion_code)
        # translate answer
        answer_code = item.findtext('value')
        if answer_code in questions[question_code]['answers']:
            item.find('value').text = questions[question_code]['answers'][
                answer_code]['translated_answer_code']

# tree.write('survey-translated.lss', xml_declaration=True, encoding="UTF-8")
tree.write(output_new_lss_file_name, xml_declaration=True, encoding="UTF-8")


# Abrir csv de dados original e gerar um traduzido
file_name_part_list = input_csv_original_file_name.split('input')
file_name_part_list = file_name_part_list[0] + 'output' + \
                      file_name_part_list[1]
file_name_part_list = file_name_part_list.split('.')
output_new_csv_file_name = file_name_part_list[0] + "_new." + \
                            file_name_part_list[1]

original_data_file = open(input_csv_original_file_name, 'r').readlines()
translated_data_file = open(output_new_csv_file_name, 'w')

for index, row in enumerate(original_data_file):
    if index == 1:
        for question in questions:
            if not questions[question]['subquestions']:
                if question in row:
                    row = row.replace(
                        question,
                        questions[question]['translated_question_code'])
            else:
                for subquestion in questions[question]['subquestions']:
                    if question + '_' + subquestion in row:
                        row = row.replace(
                            question + '_' + subquestion,
                            questions[question]['translated_question_code'] + '_' +
                            questions[question]['subquestions'][subquestion]['translated_subquestion_code'])

    translated_data_file.writelines(row)

print("Finished")
