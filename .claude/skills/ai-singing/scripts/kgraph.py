import onnx, onnx.helper as h, sys
M = 'models/kokoro-v1.0.onnx'
DUR, F0P, NP = '/encoder/Clip_output_0', '/encoder/F0_proj/Conv_output_0', '/encoder/N_proj/Conv_output_0'
def build(rep, outs, name):
    m = onnx.load(M); g = m.graph
    for n in g.node:
        for k, x in enumerate(n.input):
            if x in rep: n.input[k] = rep[x]
    for v in rep.values(): g.input.append(h.make_tensor_value_info(v, onnx.TensorProto.FLOAT, None))
    for t in outs: g.output.append(h.make_empty_tensor_value_info(t))
    onnx.save(m, f'models/{name}.onnx')
build({}, [DUR, F0P, NP], 'kokoro_probe')
build({DUR: 'dur_in', F0P: 'f0_in'}, [NP], 'kokoro_sing')
build({DUR: 'dur_in', F0P: 'f0_in', NP: 'n_in'}, [], 'kokoro_singn')
