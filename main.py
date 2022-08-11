from data        import Instr, Label
from optimizer   import optimize1
from stackir2ssa import sir2ssa
from utils       import *

# sir_functions = {
#   'main': [
#     Instr('ldloc', 'i32', loc=0),
#     Instr('ldc', 'i32', value=4),
#     Instr('div', 'i32'),
#   
#     Instr('ret', 'i32')
#   ]
# }
# 
# ssa_functions = { fn_name: sir2ssa(fn_body) for fn_name, fn_body in sir_functions.items() }

ssa_functions = {
  'main': {
    'l0': [
      Instr('stloc', 'void', loc=0, value=Instr('const', 'i32', value=1)),
      Instr('ret', 'void',
        value=Instr('add', 'i32',
          l=Instr('const', 'i32', value=2),
          r=Instr('ldloc', 'i32', loc=0)
        )
      )
    ]
  }
}

o1_passes, o1_functions = optimize1(ssa_functions, 'main')

# print('sir =', dict_prettyrepr(sir_functions, use_custom_repr=sir_pretty_repr), end='\n\n')
print('ssa =', dict_prettyrepr(ssa_functions, use_custom_repr=ssa_pretty_repr), end='\n\n')
print(f'ssa-o1(passes={o1_passes}) =', dict_prettyrepr(o1_functions, use_custom_repr=ssa_pretty_repr), end='\n\n')