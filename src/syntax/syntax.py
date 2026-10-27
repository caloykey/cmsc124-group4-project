def check_syntax(tokens):
    
    syntax_flag = 0 # if 1, triggers syntax error

    if tokens[0]['lexeme'] == 'HAI':
        print('correct start')
    
    if tokens[len(tokens) -  1]['lexeme'] == 'KTHXBYE':
        print('correct end')
