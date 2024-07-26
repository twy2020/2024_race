[basic]
type = awnn
param =./Number_int8.param
bin =./Number_int8.bin

[inputs]
input0 = 224,224,3,127.5, 127.5, 127.5,0.0078125, 0.0078125, 0.0078125

[outputs]
output0 = 7,7,75

[extra]
outputs_scale =
inputs_scale=
