from data  import Instr, Label
from copy  import deepcopy

def sir2ssa(sir):
  '''
  This function converts a stack based ir chunk into a single static assignment one

  * Chunk = piece of ir
  * Ir    = intermediate representation
  '''

  '''
  While a stack based ir can be stored in a linear array, a single static assignment cannot because
  it has to store small chunk of code inside blocks (reacheable using branches or jumps)
  '''
  
  i                 = 0            # the indexer for sir
  ssa               = { 'l0': [] } # the ssa representation result
  block             = ssa['l0']    # a ref to the current ssa block (default is the main block)
  vstack            = []           # a virtual stack simulating load (ld) and pop sir instructions
  chunks_to_convert = []           # waitlist for chunks to convert (a chunk is usually appended to this list after a jmpf/jmpt)
  blocks_remapping  = {}           # sir labels to ssa blocks name remapping

  def convert_instr_into_block(b, instr):
    nonlocal i, block

    match instr.code:
      case 'ldloc':
        vstack.append(instr)

      case 'ldc':
        vstack.append(Instr('const', instr.typ, value=instr.value))
      
      case 'add' | 'sub' | 'mul' | 'div' | 'less' | 'shl' | 'shr':
        r = vstack.pop()
        l = vstack.pop()
        vstack.append(Instr(instr.code, instr.typ, l=l, r=r))
      
      case 'neg':
        vstack.append(Instr(instr.code, instr.typ, value=vstack.pop()))
      
      case 'stloc':
        b.append(Instr('stloc', 'void', loc=instr.loc, value=vstack.pop()))
      
      case 'ret':
        b.append(Instr('ret', 'void', value=vstack.pop() if instr.typ != 'void' else None))

      case 'jmp':
        b.append(Instr('goto', 'void', target=blocks_remapping[instr.target]))
      
      case 'pop':
        b.append(vstack.pop())

      case 'jmpf':
        # value to check
        to_check = vstack.pop()
        t = f'l{len(ssa)}'
        f = f'l{len(ssa) + 1}'

        # adding the else block to the remapping table (to let future `jmp` to remap a sir label into a ssa block name)
        blocks_remapping[instr.target] = f

        # emitting a branch instruction
        b.append(Instr('branch', 'void', value=to_check, T=t, F=f))

        # calculating the index of the label into the sir chunk
        label_index = sir.index(Label(instr.target))

        # appending an empty ssa block for the true branch
        ssa[t] = []
        # inserting it into the waiting list (it will be evaluated lately)
        chunks_to_convert.append((t, sir[i+1:label_index]))

        # moving to the label index (i += 1 in the caller is gonna skip it, so the label won't be processed by the caller cycle)
        i = label_index

        # appending an empty list for the else block
        ssa[f] = []
        # using the else block as main one
        block = ssa[f]
      
      case _:
        raise ValueError(f'unknown instr code `{instr.code}`')

  # iterating instructions
  while i < len(sir):
    convert_instr_into_block(block, sir[i])

    # moving to the next chunk instruction
    i += 1

  # converting remaining blocks (previously inserted in the waiting list)
  for block_name, chunk in chunks_to_convert:
    # iterating chunk instructions
    i = 0
    while i < len(chunk):
      convert_instr_into_block(ssa[block_name], chunk[i])

      # moving to the next chunk instruction
      i += 1
  
  assert len(vstack) == 0
  
  return ssa