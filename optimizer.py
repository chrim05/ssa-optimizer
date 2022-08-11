from copy import deepcopy
from math import sqrt
from data import Instr

MAIN_CLASS_OPS = ['add', 'sub']
SUB_CLASS_OPS = ['mul', 'div']
BIN_OPS = MAIN_CLASS_OPS + SUB_CLASS_OPS + ['less'] + ['shl', 'shr']
INSTR_WITH_POSSIBLE_SIDEEFFECTS = ['call']
USELESS_OPS_AS_INSTR = BIN_OPS + ['neg', 'const', 'ldloc']

def fold_op(op, l, r):
  match op:
    case 'add': return l + r
    case 'sub': return l - r
    case 'mul': return l * r
    case 'div': return l / r

def op_of_same_class(opl, opr):
  '''
  This function returns whether `opl` and `opr` are both of the same op class (+- are of the same, */ are of the same)
  '''

  return (opl in MAIN_CLASS_OPS and opr in MAIN_CLASS_OPS) or (opl in SUB_CLASS_OPS and opr in SUB_CLASS_OPS)

def is_power_of_two(n):
  '''
  This functions returns whether `n` is a power of 2
  '''

  # this approach uses bit manipulation
  # took from https://stackoverflow.com/a/57025941
  return (n & (n-1) == 0) and n != 0

def op_times_op(opl, opr):
  '''
  This function returns op * op, examples:
  * `-` * `-` -> `+`
  * `-` * `+` -> `-`
  * `+` * `-` -> `-`
  * `+` * `+` -> `+`

  * `/` * `/` -> `*`
  * `/` * `*` -> `/`
  * `*` * `/` -> `/`
  * `*` * `*` -> `*`
  '''

  assert op_of_same_class(opl, opr)

  return {
    'addadd': 'add',
    'addsub': 'sub',

    'subsub': 'add',
    'subadd': 'sub',

    'mulmul': 'mul',
    'muldiv': 'div',
    
    'divmul': 'div',
    'divdiv': 'mul',
  }[opl + opr]

def fold_bintree(tree):
  '''
  This function tries to recursively fold a binary tree instruction supporing the following patterns (assuming `n` is const and `x` is var):
  * `n +-*/ n` -> `n`

  * `n +- (x +- n)` -> `n +- x`
  * `n */ (x */ n)` -> `n */ x`

  * `(x +- n) +- n` -> `x +- n`
  * `(x */ n) */ n` -> `x */ n`

  * `x +- 0` -> x
  * `0 + x`  -> x
  * `0 - x`  -> -x
  * `x * 0`  -> 0
  * `0 * x`  -> 0
  * `0 / x`  -> 0

  * `x * 1`  -> x
  * `1 * x`  -> x
  * `x / 1`  -> x
  '''

  # tracking this function changed data
  changed = False

  # folding recursively left node
  if tree.l.code in BIN_OPS:
    t, tree.l = fold_bintree(tree.l)
    changed += t

  # folding recursively right node
  if tree.r.code in BIN_OPS:
    t, tree.r = fold_bintree(tree.r)
    changed += t
  
  # folding `n +-*/ n`
  if tree.r.code == 'const' and tree.l.code == 'const':
    tree = Instr('const', tree.typ, value=int(fold_op(tree.code, tree.l.value, tree.r.value)))
    changed = True
  
  # this operation has just been completely folded and does not need other checkings
  if tree.code not in BIN_OPS:
    return changed, tree
  
  # folding `n +- (x +- n)` and `n */ (x */ n)` pattern
  if tree.l.code == 'const' and tree.r.code in BIN_OPS and (tree.r.r.code == 'const' or tree.r.l.code == 'const') and op_of_same_class(tree.code, tree.r.code):
    # folding the right node of the right node with the left node
    tree.l = Instr('const', tree.typ, value=fold_op(op_times_op(tree.code, tree.r.code) , tree.l.value, tree.r.r.value if tree.r.r.code == 'const' else tree.r.l.value))
    # removing the const code of the right node
    tree.r = tree.r.r if tree.r.r.code != 'const' else tree.r.l

    changed = True
  
  # folding `(x +- n) +- n` and `(x */ n) */ n` pattern
  if tree.r.code == 'const' and tree.l.code in BIN_OPS and (tree.l.r.code == 'const' or tree.l.l.code == 'const') and op_of_same_class(tree.code, tree.l.code):
    # folding the right node of the right node with the left node
    tree.r = Instr('const', tree.typ, value=fold_op(op_times_op(tree.code, tree.l.code), tree.r.value, tree.l.r.value if tree.l.r.code == 'const' else tree.l.l.value))
    # removing the const code of the right node
    tree.l = tree.l.r if tree.l.r.code != 'const' else tree.l.l

    changed = True
  
  # converting special situations with `0` and `1` at right
  if tree.r.code == 'const':
    match tree.r.value:
      # `x +- 0` -> x
      # `x * 0`  -> 0
      case 0:
        old, tree = tree, { 'add': tree.l, 'sub': tree.l, 'mul': tree.r, 'div': tree }[tree.code]
        changed += old != tree

      # `x * 1`  -> x
      # `x / 1`  -> x
      case 1:
        old, tree = tree, { 'add': tree, 'sub': tree, 'mul': tree.l, 'div': tree.l }[tree.code]
        changed += old != tree
  
  # converting special situations with `0` and `1` at left
  if tree.l.code == 'const':
    match tree.l.value:
      # `0 + x`  -> x
      # `0 - x`  -> -x
      # `0 * x`  -> 0
      # `0 / x`  -> 0
      case 0:
        old, tree = tree, { 'add': tree.r, 'sub': Instr('neg', tree.typ, value=tree.r), 'mul': tree.l, 'div': tree.l }[tree.code]
        changed += old != tree

      # `1 * x`  -> x
      case 1:
        old, tree = tree, { 'add': tree, 'sub': tree, 'mul': tree.r, 'div': tree }[tree.code]
        changed += old != tree
  
  return changed, tree

def collect_instructions_with_sideeffects(instr):
  '''
  This function recursively walks through `instr`'s fields (`instr` is gonna be removed by the caller for uselessness)
  looking for instructions with sideeffects to keep
  '''
  
  instructions = []

  for field_name, field in instr.__dict__.items():
    # skipping field `code`, `typ` etc..
    if isinstance(field, Instr):
      # whether the field could have side effects
      if field.code in INSTR_WITH_POSSIBLE_SIDEEFFECTS:
        instructions.append(field.code)
      # otherwise search for instructions with sideeffects inside it
      else:
        instructions.extend(collect_instructions_with_sideeffects(field))
  
  return instructions

def get_faster_corresponding_instruction(instr):
  '''
  This function tries to find a faster corresponding instruction to the one given, otherwise returns the same
  '''

  # tracking whether this function changed data
  changed = False

  # converting `n * x` and `x * n` where `n` is a power of 2 into a left bit shifting operation
  if instr.code == 'mul':
    # `n` is at the left of the node
    if instr.l.code == 'const' and is_power_of_two(instr.l.value):
      # converting `n` into a value for left bit shifting `x` and getting the same result
      instr.l.value = int(sqrt(instr.l.value))
      instr = Instr('shl', instr.typ, l=instr.r, r=instr.l)

      changed = True

    # `n` is at the right of the node
    elif instr.r.code == 'const' and is_power_of_two(instr.r.value):
      # converting `n` into a value for left bit shifting `x` and getting the same result
      instr.r.value = int(sqrt(instr.r.value))
      instr = Instr('shl', instr.typ, l=instr.l, r=instr.r)

      changed = True
  
  # converting `x / n` where `n` is a power of 2 into a right bit shifting operation
  if instr.code == 'div' and instr.r.code == 'const' and is_power_of_two(instr.r.value):
    # converting `n` into a value for right bit shifting `x` and getting the same result
    instr.r.value = int(sqrt(instr.r.value))
    instr = Instr('shr', instr.typ, l=instr.l, r=instr.r)

    changed = True
  
  return changed, instr

def constfolding_plus_math_replacing_plus_rm_useless(ssa):
  '''
  This function walks through instructions (instructions in ssa form are tree-structured, so we even need to walk through instruction's fields)
  and replaces them with a folded version

  Secondary features:
  * Replaces some math operations with a simplified one (usually faster)
  * Removes useless operations keeping instructions with sideeffects
  '''

  # tracking whether this algorithm changed data
  changed = False

  for block_name, block in ssa.items():
    new_block = []

    for i, instr in enumerate(block):
      # useless instructions aren't added to the new block
      if instr.code not in USELESS_OPS_AS_INSTR:
        new_block.append(instr)
      # they are passed to a function which is gonna recursively walk them to collect all instructions to keep (because they have sideeffects, like `call`)
      else:
        new_block.extend(collect_instructions_with_sideeffects(instr))
        changed = True

      # ssa instructions are tree-structured, so we need to check every field, whether it's an instruction and it's a bin op we try to fold it
      for field_name, field in instr.__dict__.items():
        # checking whether the field is an instruction and a bin op
        if isinstance(field, Instr) and field.code in BIN_OPS:
          # replacing the field with the folded version (actually `fold_bintree` tries to fold it, otherwise it returns the same instr)
          changing1, instr.__dict__[field_name] = fold_bintree(field)

          # replacing the field with the corresponding faster one
          changing2, instr.__dict__[field_name] = get_faster_corresponding_instruction(field)

          # updating the changes tracker
          changed += changing1 + changing2
    
    # replacing the old block with the newer
    ssa[block_name] = new_block
  
  return changed

def remove_dead_code(ssa):
  changed = False

  return changed

def optimize1(ssa_functions, main):
  '''
  This function returns a copy of ssa with following changes:
  * Constant operations are folded
  * Some math instructions are replaced with faster (multiplications -> bit shift)
  * Useless operations without sideeffects are removed (redundant code elimination)

  * [TODO] Unreachable code elimination
  * [TODO] Dead code elimination
  * [TODO] Non-recursive functions are inlined where possible
  * [TODO] Functions with constant args are compile time executed, excluding for instructions with sideeffects, which are keept
  * [TODO] Loop unrolling (cycles with a an compile time known lifetime)
  * [TODO] Recursive functions are converted into a cycle where possible
  '''

  # traking passes, starting from -1 because the last pass doesn't actually change data (it just checks there's nothing to change anymore)
  passes = -1

  # making sure to mutate a copy, keeping old unoptimized data
  ssa_functions = deepcopy(ssa_functions)

  # not caring about algorithm calling order, they are called until the data is not gonna change anymore
  while True:
    passes += 1

    # starting to optimize the main function
    ssa     = ssa_functions[main]
    # tracking whether in this cycle some algorithm changed data
    changed = False

    # constant folding + math simplfication + useless ops removal (excluding instructions with sideeffects)
    changed += constfolding_plus_math_replacing_plus_rm_useless(ssa)

    # dead code is deleted
    changed += remove_dead_code(ssa)

    # when the data is not goin to change anymore, the cycle has to stop
    if not changed:
      break

  return passes, ssa_functions