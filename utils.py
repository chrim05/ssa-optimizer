from data import Instr

def list_prettyrepr(l, indent_size=2, brack_indent_size=0, indent_first_brack=False, use_custom_repr=None):
  '''
  This function pretty prints a list

  Example:
    - `repr(l)`            -> `'[0, 1, 2, 3]'`
    - `list_prettyrepr(l)` ->
      * `'[`
        * `.. 0,`
        * `.. 1,`
        * `.. 2,`
        * `.. 3,`
      * `]'`
  '''

  # converting indent level into real indent
  indent = ' ' * indent_size
  brack_indent = ' ' * brack_indent_size
  s = ''

  for e in l:
    r = \
        pretty_repr(e, indent_size=indent_size+2, brack_indent_size=brack_indent_size+2) \
      if use_custom_repr == None \
      else \
        use_custom_repr(e, indent_size=indent_size+2, brack_indent_size=brack_indent_size+2)

    s += f'{indent}{r},\n'
  
  return f'{brack_indent if indent_first_brack else ""}[\n' + s + f'{brack_indent}]'

def dict_prettyrepr(d, indent_size=2, brack_indent_size=0, indent_first_brack=False, use_custom_repr=None):
  '''
  This function does the same of `list_prettyrepr`, for desc look at it
  '''

  # converting indent level into real indent
  indent = ' ' * indent_size
  brack_indent = ' ' * brack_indent_size
  s = ''

  for k, v in d.items():
    r = \
        pretty_repr(v, indent_size=indent_size+2, brack_indent_size=brack_indent_size+2) \
      if use_custom_repr == None \
      else \
        use_custom_repr(v, indent_size=indent_size+2, brack_indent_size=brack_indent_size+2)

    s += f'{indent}{repr(k)}: {r},\n'
  
  return f'{brack_indent if indent_first_brack else ""}{{\n' + s + f'{brack_indent}}}'

def pretty_repr(obj, indent_size=2, brack_indent_size=0, indent_first_brack=False):
  '''
  This function returns a pretty representation of `obj`
  '''

  match obj.__class__.__name__:
    case 'dict':
      return dict_prettyrepr(obj, indent_size, brack_indent_size, indent_first_brack)
    
    case 'list':
      return list_prettyrepr(obj, indent_size, brack_indent_size, indent_first_brack)

    case _:
      # checking whether type(obj) is primitive type
      if not hasattr(obj, '__dict__'):
        return repr(obj)
      
      instance = dict_prettyrepr(obj.__dict__, indent_size, brack_indent_size, indent_first_brack=False).removeprefix('{').removesuffix('}')
      return f'{obj.__class__.__name__}(' + instance + f')'

ALPHABET = list(map(chr, range(ord('a'), ord('z') + 1)))

def ssa_chunk_to_human_readable(chunk):
  '''
  This function returns the chunk with instructions as human readable representation strings
  '''

  schunk                    = [] # the chunk with instructions as strings
  alphabet_counter          = 0  # single static assigned virtual register of ssa are named with alphabet letters
  alphabet_repeat_indicator = '' # single static assigned virtual register of ssa cannot be reassigned, so in the second use of `a` it will be `a'`
  available_var_name        = lambda: ALPHABET[alphabet_counter] + alphabet_repeat_indicator # providing a variable name

  def decompose_arg(arg_name, arg):
    '''
    This function returns a variable name referring to a bigger instruction when needed (for more readability)
    '''

    nonlocal alphabet_counter

    if not isinstance(arg, Instr):
      return f'{arg_name}={repr(arg)}'

    # converts the instr into a human readable representation as string
    match arg.code:
      case 'const':
        arg = arg.value
      
      case 'ldloc' | 'add' | 'sub' | 'mul' | 'div' | 'less' | 'branch' | 'neg' | 'shl' | 'shr':
        add_ssa_instr_to_string(arg)
        arg = available_var_name()
        alphabet_counter += 1

      case _:
        raise NotImplementedError(arg.code)
    
    return f'{arg_name}={arg}'
  
  def add_ssa_instr_to_string(instr):
    kwargs = ", ".join(map(str, (decompose_arg(k, instr.__dict__[k]) for k in filter(lambda k: k not in ["code", "typ"], instr.__dict__.keys()))))

    if instr.typ != 'void':
      schunk.append(f'{available_var_name()} = {instr.code} {instr.typ} {kwargs}')
    else:
      schunk.append(f'{instr.code} {instr.typ} {kwargs}')

  for instr in chunk:
    # when reached the letter 'z' resets the alphabet indexer and adds an indicator
    if alphabet_counter == len(ALPHABET):
      alphabet_counter = 0
      alphabet_repeat_indicator += "'"

    add_ssa_instr_to_string(instr)
  
  return schunk

def ssa_pretty_repr(ssa, indent_size=2, brack_indent_size=0, indent_first_brack=False):
  return dict_prettyrepr({ block: ssa_chunk_to_human_readable(chunk) for block, chunk in ssa.items() }, indent_size, brack_indent_size, indent_first_brack)

def sir_pretty_repr(sir, indent_size=2, brack_indent_size=0, indent_first_brack=False):
  return list_prettyrepr(map(lambda e: e.to_human_readable_sir(), sir), indent_size, brack_indent_size, indent_first_brack)