[![Build Status](https://travis-ci.com/skjerns/pyUnisens.svg?branch=master)](https://travis-ci.com/skjerns/pyUnisens)  [![Coverage Status](https://coveralls.io/repos/github/skjerns/pyUnisens/badge.svg?branch=master)](https://coveralls.io/github/skjerns/pyUnisens?branch=master)

# pyUnisens
Implementation of the Unisens data storage format

## Installation
pyUnisens can be installed via pip with
`pip install git+https://github.com/skjerns/pyUnisens`

## Quickstart

You can load any unisens object simply like this

```Python
import unisens

u = unisens.Unisens('c:/folder/dataset/') # folder containing the unisens.xml
```

Entries are saved under `.entries` can be accessed either via attribute or using the unisens object as a dictionary

```Python
print(u.entries)

# fourys to rome
signal = u.signal_bin
signal = u['signal.bin']
signal = u.entries['signal.bin']
signal = u[0]
```

Data can be loaded (if datatypeis supported, ie a standard numpy dtype) via `data= signal.get_data()`

You can add Entries simply:

```Python
import numpy as np
from unisens import SignalEntry
data = np.random(2, 2560)
s = SignalEntry(parent=u)
s.set_data(data, sampleRate=256, contentClass='EEG')

u.add_entry(s)

u.save()
```

more documentation will follow soon.

please report any bugs or improvements via github issues.