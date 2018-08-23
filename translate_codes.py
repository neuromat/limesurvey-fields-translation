#!/usr/bin/python3

"""
Generates new files to LimeSurvey with codes (questions, subquestions,
answers), translated
Entries: spreadsheet translated/reviewd, file with original questionnaire
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
import getopt
import sys
import os
from xml.etree import ElementTree as ETree
from shutil import copyfile

import pandas


def parse_options(argv):
    lss_input_file = ''
    answers_input_file = ''
    spreadsheet_input_file = ''
    try:
        opts, args = getopt.getopt(
            argv, 'hl:a:r:', ['lss=', 'answer=', 'reviewed=']
        )
    except getopt.GetoptError:
        print('translate_codes.py -l <inputfile1> -a <inputfile2> -r '
              '<inputfile3>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('translate_codes.py -l <inputfile1> -a <inputfile2> -r '
                  '<inputfile3>')
            sys.exit(1)
        elif opt in ('-l', '--lss'):
            lss_input_file = arg
        elif opt in ('-a', '--answer'):
            answers_input_file = arg
        elif opt in ('-r', '--reviewed'):
            spreadsheet_input_file = arg

    if lss_input_file == '' or answers_input_file == '' or \
            spreadsheet_input_file == '':
        print('translate_codes.py -l <inputfile1> -a <inputfile2> -r '
              '<inputfile3>')
        sys.exit(2)

    return [lss_input_file, answers_input_file, spreadsheet_input_file]


def main(argv):
    lss_input_file, answers_input_file, spreadsheet_input_file = \
        parse_options(argv)

    # read spreadsheet translated
    with open(spreadsheet_input_file, 'r') as f:
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
                    print('It\'s not supposed to have questions with same '
                          'code')
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
                if current_subquestion_code in \
                        questions[current_question]['subquestions']:
                    print('It\'s not supposed to have subquestions with same '
                          'code')
                else:
                    questions[current_question]['subquestions'][current_subquestion_code] = \
                        {
                            'translated_subquestion_code': translated_subquestion_code,
                            'subquestion_id': question_id
                        }
            elif item == "answer":
                current_answer_code = line[8]
                translated_answer_code = line[9]
                if current_answer_code in \
                        questions[current_question]['answers']:
                    print('It\'s not supposed to have answers with same code')
                else:
                    questions[current_question]['answers'][current_answer_code] = \
                        {'translated_answer_code': translated_answer_code}

    # spreadsheet validations

    # open original lss and generates a copy to be translated
    file_name = lss_input_file.split('.')
    output_new_lss_file_name = file_name[0] + "_new." + file_name[1]
    copyfile(lss_input_file, "temp_lss.lss")

    tree = ETree.parse("temp_lss.lss")

    for item in tree.iterfind('questions/rows/row'):
        # fields to read: gid, qid, language, question_order, type, title
        # (question_code), question (description, depends of the language)
        question_code = item.findtext('title')
        if question_code in questions:
            item.find('title').text = \
                questions[question_code]['translated_question_code']

        # translate formulas and texts
        if item.findtext('type') in ("*", "X"):
            original_text = item.findtext('question')
            for question in questions:
                if question in original_text:
                    item.find('question').text = \
                        item.findtext('question').replace(
                            question,
                            questions[question]['translated_question_code']
                        )

        # Translation of relevance field (related to conditions)
        # Examples of relevance:
        #   (1) 1
        #   (2) ((256242X320X16516.NAOK == "S"))
        #   (3) ((256242X320X16517Outro.NAOK == "Y"))
        #   (4) ((256242X319X16495.NAOK == "D" or 256242X319X16495.NAOK == "DE"))
        #   (5) ((256242X322X17689Trofismo#1.NAOK == "P"))
        #
        #   *Example (1): não há nada para fazer
        #   *Example (2): questão 16516 não contém subquestion, temos que
        # traduzir somente a resposta
        #   *Example (3): questão 16517 contém subquestion, temos que
        # traduzir a subquestion e a resposta
        #   *Example (4): podemos encontrar mais do que uma parte para traduzir
        #   *Example (5): às vezes a subquestion vem com um sufixo '#'

        relevance = item.findtext('relevance')
        current_pos = 0
        naok_pos = relevance.find('NAOK', current_pos)

        while naok_pos != -1:
            # traducao do subquestion
            pieces = relevance[current_pos:naok_pos].split('X', maxsplit=2)
            # ultima parte pode conter subquestion_code
            question_id = pieces[-1][:5]
            subquestion_code = pieces[-1][5:].split('.')[0].split('#')[0]
            if question_id in question_ids:
                question_code = question_ids[question_id]
                if question_code in questions:
                    if questions[question_code]['subquestions']:
                        pieces[-1] = \
                            pieces[-1].replace(
                                subquestion_code,
                                questions[question_code]['subquestions'][subquestion_code]['translated_subquestion_code']
                            )
                        relevance = relevance[:current_pos] + 'X'.join(pieces) + relevance[naok_pos:]
                        item.find('relevance').text = relevance
                        naok_pos = relevance.find('NAOK', current_pos)

            # traducao do answer
            if question_id in question_ids:
                question_code = question_ids[question_id]
                if question_code in questions:
                    pieces = relevance[naok_pos + 9:].split('"')
                    answer_code = pieces[0]
                    if 'answers' in questions[question_code]:
                        if answer_code in questions[question_code]['answers']:
                            pieces[0] = \
                                questions[question_code]['answers'][answer_code]['translated_answer_code']
                            relevance = \
                                relevance[:naok_pos + 9] + '"'.join(pieces)
                            item.find('relevance').text = relevance
                            naok_pos = relevance.find('NAOK', current_pos)
                    else:
                        print("question %s does not have answers")

            # next 'NAOK'
            current_pos = naok_pos + 1
            naok_pos = relevance.find('NAOK', current_pos)

    for item in tree.iterfind('subquestions/rows/row'):
        # fields to read: gid, language, qid (subquestion id),
        # parent_qid (question id), type (corresponde ao tipo da pergunta ou
        # da subpergunta), title (subquestion_code), question (description,
        # depends of the language), question_order
        question_id = item.findtext('parent_qid')
        if question_id in question_ids:
            question_code = question_ids[question_id]
            subquestion_code = item.findtext('title')
            if subquestion_code in questions[question_code]['subquestions']:
                item.find('title').text = \
                    questions[question_code]['subquestions'][subquestion_code]['translated_subquestion_code']

    for item in tree.iterfind('answers/rows/row'):
        # fields to read: qid (question id), code (answer code)
        question_id = item.findtext('qid')
        if question_id in question_ids:
            question_code = question_ids[question_id]
            answer_code = item.findtext('code')
            if answer_code in questions[question_code]['answers']:
                item.find('code').text = \
                    questions[question_code]['answers'][answer_code]['translated_answer_code']

    for item in tree.iterfind('conditions/rows/row'):
        question_id = item.findtext('cqid')
        if question_id in question_ids:
            question_code = question_ids[question_id]
            # translate subquestion
            if questions[question_code]['subquestions']:
                field_name = item.findtext('cfieldname')
                fields = field_name.split('X', maxsplit=2)
                pieces = fields[-1].split('#')
                subquestion_code = pieces[0].replace(
                    questions[question_code]['question_id'], ''
                )
                if subquestion_code \
                        in questions[question_code]['subquestions']:
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

    tree.write(
        output_new_lss_file_name, xml_declaration=True, encoding="UTF-8"
    )

    # Open original csv data file and generate translated new one
    file_name = answers_input_file.split('.')
    output_new_csv_file_name = file_name[0] + "_new." + file_name[1]

    original_data_file = open(answers_input_file, 'r').readlines()
    translated_data_file = open(output_new_csv_file_name, 'w')

    for index, row in enumerate(original_data_file):
        if index == 0:
            translated_data_file.writelines(row)  # TODO: improve?
        if index == 1:
            # TODO:
            # multiple choice questions (type M) (not multiple questions
            # with comments) is not captured here when there is a response
            # with other option. The question code is not translated,
            # and the imported responses will present error in this option.
            # By now, correcting in the own new reponses csv generated.
            for question in questions:
                if not questions[question]['subquestions']:
                    if question in row:
                        row = row.replace(
                            question,
                            questions[question]['translated_question_code'])
                else:
                    for subquestion in questions[question]['subquestions']:
                        if question + '_' + subquestion in row:
                            # Needed to add '\t' for catching question + '_' +
                            # subquestion exactly. Example:
                            #   lisneurolisenervo_1 -> mulLysisNerve_DS
                            #   lisneurolisenervo_10 -> mulLysisNerve_DS0
                            row = row.replace(
                                question + '_' + subquestion + '\t',
                                questions[question]['translated_question_code']
                                + '_' +
                                questions[question]['subquestions'][
                                    subquestion][
                                    'translated_subquestion_code'] + '\t'
                            )
                            # replace array questions
                            # (e.g. opcSensi_Cinestesia_0)
                            row = row.replace(
                                question + '_' + subquestion + '_',
                                questions[question]['translated_question_code']
                                + '_' +
                                questions[question]['subquestions'][
                                    subquestion][
                                    'translated_subquestion_code'] + '_'
                            )
                            # replace questions with comments
                            row = row.replace(
                                question + '_' + subquestion + 'comment',
                                questions[question]['translated_question_code']
                                + '_' +
                                questions[question]['subquestions'][subquestion][
                                    'translated_subquestion_code'] + 'comment'
                            )
                # replace multiple questions with
                # "<question>_other", e.g. "lisDorPr_other"
                if question + '_other' in row:
                    row = row.replace(
                        question + '_other',
                        questions[question]['translated_question_code']
                        + '_other'
                    )
            translated_data_file.writelines(row)

    # Check if all questions codes (not subquestions or answers) was
    # translated in new vv file
    # TODO

    # Translate answers in the new vv file
    answers = pandas.read_table(answers_input_file, skiprows=1)
    for column in answers:
        question = [q for q in questions if q in column]
        if not question:
            continue
        else:
            question = question[0]
            if not questions[question]['answers']:
                continue
            else:
                for index, answer in enumerate(answers[column]):
                    if answer in questions[question]['answers']:
                        answers[column][index] = questions[question]['answers'][
                            answer]['translated_answer_code']
    answers.to_csv('temp_translated_data_file.csv', sep='\t', index=False,
                   header=False)
    temp_translated_data_file = open('temp_translated_data_file.csv', 'r')
    for index, row in enumerate(temp_translated_data_file):
        translated_data_file.writelines(row)
    translated_data_file.close()

    os.remove('temp_translated_data_file.csv')
    os.remove('temp_lss.lss')
    print("Finished")


if __name__ == "__main__":
    main(sys.argv[1:])
