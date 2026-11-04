"""Copy frozen inference functions exactly; avoid loading old retrieval pickle stores."""
from pathlib import Path
import ast

P=Path(__file__).resolve().parents[2];F=Path(__file__).parent
source=(P/'web/backend/project01_core/foundation.py').read_text(encoding='utf-8');tree=ast.parse(source)
names=['digest','file_sha','read_json','validate_profile','transform_profile','mlp_forward','probability']
parts=[ast.get_source_segment(source,next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)) for name in names]
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Runtime')
predict=ast.get_source_segment(source,next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='predict'))
init='''class FrozenRisk:
    def __init__(self,package):
        self.package=Path(package)
        manifest=read_json(self.package/'manifest.json')
        needed={'model.npz','preprocessing.json','profile_schema.json','model_config.json'}
        hashes={r['path']:r['sha256'] for r in manifest['files']}
        for name in needed:
            if file_sha(self.package/name)!=hashes[name]:raise ValueError('Frozen risk asset hash mismatch')
        self.schema=read_json(self.package/'profile_schema.json');self.preprocessing=read_json(self.package/'preprocessing.json')
        self.config=read_json(self.package/'model_config.json')
        with np.load(self.package/'model.npz',allow_pickle=False) as archive:self.weights={name:archive[name].copy() for name in archive.files}
        if self.preprocessing['input_columns']!=self.schema['feature_order']:raise ValueError('Feature order mismatch')
        self.model_hash=file_sha(self.package/'model.npz')

'''
import textwrap
text='from pathlib import Path\nimport hashlib,json,math\nimport numpy as np\n\n'+'\n\n'.join(parts)+'\n\n'+init+textwrap.indent(predict,'    ')+'\n'
ast.parse(text);target=F/'authoring/risk.py'
if target.exists():raise RuntimeError('Port exists')
target.write_text(text,encoding='utf-8');print('7 frozen helper functions and original predict copied unchanged')
