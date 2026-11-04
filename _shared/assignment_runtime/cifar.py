"""Explicit CIFAR binary adapter; never pretend the binary archive is Python pickle."""
from pathlib import Path
import tarfile
import numpy as np

CLASS_NAMES=["airplane","automobile","bird","cat","deer","dog","frog","horse","ship","truck"]


def read_binary(path, *, include_test=False, train_limit=None):
    """Read canonical batch/row order into NHWC pixels. Default never opens TEST records."""
    train_x=[]
    train_y=[]
    test_x=test_y=None
    with tarfile.open(Path(path),"r:gz") as archive:
        wanted=[f"cifar-10-batches-bin/data_batch_{i}.bin" for i in range(1,6)]
        if include_test: wanted.append("cifar-10-batches-bin/test_batch.bin")
        remaining=train_limit
        for name in wanted:
            if "test_batch" not in name and remaining is not None and remaining<=0: continue
            member=archive.getmember(name)
            assert member.size==10000*3073
            with archive.extractfile(member) as handle:
                if "test_batch" in name:
                    payload=handle.read()
                else:
                    count=min(10000,remaining) if remaining is not None else 10000
                    payload=handle.read(count*3073)
            records=np.frombuffer(payload,dtype=np.uint8).reshape(-1,3073)
            labels=records[:,0].astype(np.int64)
            pixels=records[:,1:].reshape(-1,3,32,32).transpose(0,2,3,1).copy()
            assert labels.min()>=0 and labels.max()<10
            if "test_batch" in name: test_x,test_y=pixels,labels
            else:
                train_x.append(pixels)
                train_y.append(labels)
                if remaining is not None: remaining-=len(labels)
    return np.concatenate(train_x),np.concatenate(train_y),test_x,test_y
