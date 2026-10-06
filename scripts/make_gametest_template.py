"""Write a minimal empty NBT scene for cabinet integration tests (no dependencies)."""
import gzip
import struct
from pathlib import Path

def name(value):
    encoded=value.encode('utf-8')
    return struct.pack('>H',len(encoded))+encoded

def tag(kind,label,payload): return bytes([kind])+name(label)+payload

integer=lambda value: struct.pack('>i',value)
root=bytes([10])+name('')
root+=tag(3,'DataVersion',integer(3955))
root+=tag(9,'size',bytes([3])+integer(3)+b''.join(integer(n) for n in (7,6,7)))
root+=tag(9,'entities',bytes([10])+integer(0))
root+=tag(9,'blocks',bytes([10])+integer(0))
root+=tag(9,'palette',bytes([10])+integer(1)+tag(8,'Name',name('minecraft:air'))+bytes([0]))
root+=bytes([0])
path=Path(__file__).resolve().parents[1]/'src/main/resources/data/funpackcustom/structure/nostalgia_test.nbt'
path.parent.mkdir(parents=True,exist_ok=True)
path.write_bytes(gzip.compress(root,mtime=0))
print(path)
