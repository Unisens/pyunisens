[![Build Status](https://travis-ci.com/Unisens/pyunisens.svg?branch=master)](https://travis-ci.com/Unisens/pyunisens)  [![Coverage Status](https://coveralls.io/repos/github/Unisens/pyunisens/badge.svg?branch=master)](https://coveralls.io/github/Unisens/pyunisens?branch=master)

# pyunisens
Implementation of the Unisens data storage format

## Installation
Stable version can be installed via `pip install pyunisens`

or most recent version via `pip install git+https://github.com/Unisens/pyunisens`

`pyunisens` is running on Python 3.6+

## Quickstart

You can load any unisens object simply like this

```Python
import unisens

u = unisens.Unisens('c:/folder/dataset/') # folder containing the unisens.xml
```

Entries are saved under `.entries` can be accessed either via attributes or using the unisens object as a dictionary

```Python
print(u.entries)

# four ways to Rome
signal = u.signal_bin
signal = u['signal.bin']
signal = u.entries['signal.bin']
signal = u[0]

# shortcuts also work, if they are not ambiguous
signal = u.signal
signal = u['signal']

print(type(signal))
# signalEntry
```

Data can be loaded (if datatypeis supported, ie a standard numpy dtype) via `data= signal.get_data()`

You can add Entries simply by

```Python
import numpy as np
from unisens import SignalEntry

data = np.random(2, 2560)
s = SignalEntry(id='eeg.bin', parent=u)
# parent=u makes sure the signal is added to this Unisens object
# saving the data to eeg.bin
s.set_data(data, sampleRate=256, contentClass='EEG')

u.save() # will update the unisens.xml
```

## Documentation
More documentation can be found at 
[API-OVERVIEW.md](API-OVERVIEW.md) and in the function descriptors


## Bug reports / feedback
Please report any bugs or improvements via a Github issue.
