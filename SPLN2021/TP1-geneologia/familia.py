#!/usr/bin/python3
#from jjcli import *
import sys
import requests
import re
import json
import shelve



#http://pagfam.geneall.net/3418/pessoas_search.php
r = requests.get('http://pagfam.geneall.net/3418/pessoas.php?id=1075983')

#Percorre lista de páginas http://pagfam.geneall.net/3418/pessoas.php?id= e constroi dicionário id -> { 'nome' : 'Ricardo'}
def get_persons() -> dict:
    persons = {}
    start=0
    for i in range(5):
        page = requests.get(f'http://pagfam.geneall.net/3418/pessoas_search.php?start={start}&orderby=&sort=&idx=0&search=')
        #print('request.url: ', page.url, 'request.headers: ', page.headers, 'request.text: ')
        for match in re.findall(r'<A href="pessoas\.php\?id=((\d)+)">((.|\n)*?)<\/A>', page.text):
            persons[match[0]]= {'nome' : match[2]}
        start+=30
    return persons


#Recebe dicionário e página da pessoa e extrai informação para o dicionário person_dict = {'nome' : 'nome1', 'pai': 'idpai', 'mae' :'idmae' , ...}
def extract_info(key, person_dict, page):
    #familia
    if match := re.search(r'<div align="center" class="head2" style="margin-bottom: 5px;">Família (.*?)<\/div>', page):
        person_dict['familia'] = match.group(1)

    #data+local de nascimento
    if match := re.search(r'"center">(\s{0,2}\*.*?)<nobr>(.*?)<\/nobr>', page):
        person_dict['local_nascimento'] = match.group(1).strip()
        if match.group(2):
            person_dict['data_nascimento'] = match.group(2).strip()

    #data+local de morte
    if match := re.search(r'("center">|<\/nobr>)(\s{0,2}\+.*?)<nobr>(.*?)<\/nobr>', page):
        person_dict['local_morte'] = match.group(2).strip()
        if match.group(3):
            person_dict['data_morte'] = match.group(3).strip()
    
    #pai/mae
    for match in re.findall(r'<B>(Pai|Mãe):<\/B>\s?<A\sHREF=.*?id=(\d+)>(.*?)<\/A>', page):
        person_dict[match[0].lower()] = match[1]

    #notas (falta apanhar multiplas notas)
    if match := re.search(r'<div class="marcadorP" style="margin-top: 10px;">Notas<\/div><UL CLASS=txt2>\n?<LI>(.*?)<\/LI>', page):
        person_dict['notas'] = match.group(1).strip()

    #casamentos
    if match := re.search(r'<div class="marcadorP" style="margin-top: 10px;">Casamentos</div>', page):
        #casamentos multiplos
        if match := re.search(r'<div align="center"><B>Casamento I:<\/B>', page):
            casamentos = []
            for match in re.findall(r'<div align="center"><B>Casamento (I|II|III):<\/B>(.*?)(<nobr>(.*?)<\/nobr>)?<\/div><div align="center" style="margin-bottom: 15px;"><A href=pessoas\.php\?id=(.*?)>(.*?)<\/A>((.*?)<nobr>(.*?)<\/nobr>)?<\/div>', page):
                casamento = {}
                casamento['local'] = match[1].strip()
                casamento['data'] = match[3]
                casamento['pessoa_id'] = match[4]
                casamento['pessoa_nome'] = match[5].strip()
                casamentos.append(casamento)
            person_dict['casamentos']=casamentos
        #casamento singular
        else:
            if match := re.search(r'Casamentos<\/div><div align="center">((.*?)<nobr>(.*?)<\/nobr>)?<\/div><div align="center" style="margin-bottom: 15px;"><A href=pessoas\.php\?id=(\d+)>(.*?)<\/A>( \*  <nobr>(.*?)<\/nobr>)?<\/div>', page):
                casamento = {}
                casamento['local'] = match[2]
                casamento['ano'] = match[3]
                casamento['pessoa_id'] = match[4]
                casamento['pessoa_nome'] = match[5].strip()
            person_dict['casamentos']=[casamento]
    
    #filhos
    if match := re.search(r'<div class="txt2"><div class="marcadorP" style="margin-top: 10px;">Filhos</div>', page):
        filhos = []
        for match in re.findall(r'<LI><A HREF=pessoas\.php\?id=(\d+)>(.*?)<\/A>', page):
            filho = {}
            filho['filho_id'] = match[0]
            filho['filho_nome'] = match[1].strip()
            #filho['nascimento'] = match[3]
            filhos.append(filho)
        person_dict['filhos']=filhos


#Itera sobre o dicionário das pessoas e invoca extract_info(persons_dict[key], page.text) para cada uma
def get_info(persons_dict) -> dict:
    for key, value in persons_dict.items():
        page = requests.get(f'http://pagfam.geneall.net/3418/pessoas.php?id={key}')
        extract_info(key, persons_dict[key], page.text)
    return persons_dict


def searchby_key(key, gen):
    try:
        person = gen[key]
        print(json.dumps(person, ensure_ascii=False, indent=4).encode('utf8').decode())
    except:
        print('Chave desconhecida')


def searchby_name(name, gen):
    try:
        for key,person in gen.items():
            if name in person.get("nome", ""):
                print(json.dumps(person, ensure_ascii=False, indent=4).encode('utf8').decode())
    except:
        print('Nome desconhecido')


def save_shelve(gen):
    gens = shelve.open('gens.db')
    try:
        for key, value in gen.items():
            gens[key] = value
    finally:
        gens.close()


def to_json(gen):
    f = open('gen.json', 'w+')
    json_gen = json.dumps(gen, ensure_ascii=False, indent=4).encode('utf8').decode()
    f.write(json_gen)
    f.close()

def load_shelve(gen) -> dict:
    try:
        gens = shelve.open('gens.db', 'r')
        gen = dict(gens)
        gens.close()
        return gen
    except:
        print('didnt load shelve file')
        return None


def execute_cmd(line, gen):
    if cmd := re.match(r'(searchk|searchn)\s{1,3}(.+)', line):
        print('group(1): ', cmd.group(1), 'group(2): ', cmd.group(2))
        if cmd.group(1) == 'searchk':
            searchby_key(cmd.group(2), gen)
        
        elif cmd.group(1) == 'searchn':
            searchby_name(cmd.group(2), gen)

    elif cmd := re.match(r'(help|shelves|tojson)', line):
        if cmd.group(1) == 'shelves':
            save_shelve(gen)
        elif cmd.group(1) == 'help':
            print('searchk searchn shelves tojson')
        elif cmd.group(1) == 'tojson':
            to_json(gen)

    else:
        print('Comando Inválido')


def main():
    gen = {}
    if gen := load_shelve(gen):
        print('loaded shelve file')
    else:
        persons_dict = get_persons()
        print('processing ...')
        gen = get_info(persons_dict)
        print('finished')
    
    #ler stdin
    for line in sys.stdin:
        execute_cmd(line, gen)


if __name__ == "__main__":
    main()