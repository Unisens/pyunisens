[![Build Status](https://travis-ci.com/skjerns/pyunisens.svg?branch=master)](https://travis-ci.com/skjerns/pyunisens)  [![Coverage Status](https://coveralls.io/repos/github/skjerns/pyunisens/badge.svg?branch=master)](https://coveralls.io/github/skjerns/pyunisens?branch=master)

# pyunisens API overview
Get a grasp of what pyunisens can do.

## Introduction

Unisens is an XML based meta file storage format. 

Each Unisens object can contain several `Entries`

- `SignalEntry` for binary signals with at least one channel
- `ValuesEntry` for continuous values
- `EventEntry` for event-like activity that is not periodic
- `CustomEntry` for any other file type

Each `Entry` has attributes (accessible via `.attrib`) and can be parent to other Entries (accessible via `._entries`).


## Entry

An `Entry` is the base class of Unisens from which all other classes inherit. Entries can have sub-entries, which is called a child. The most important Entry is the `Unisens` object itself. `Unisens` is the upper most parent and contains all other Entries.

### Attributes
Entries can have attributes (saved as XML attributes) that give further meta information about the entry, e.g. comments, additional information, sample rates, etc.

Attributes are saved internally under `.attrib`, but can be accessed and set just as any regular Python attribute

##### Setting attributes

```Python
### How to set attributes
# either using Python attribute syntax
u = unisens.Unisens('.')
u.name = 'pi'
u.pi = 3.14
u.comment = 'this is not edible'

# using the set method
u.set_attrib('name', 'pi')

# using the attrib-dictionary
u.attrib['name'] = 'pi'

# be aware, attributes are saved in XML as strings, so they might need to be
# converted back to int/float when reloading the Unisens object.
```

##### Removing attributes

```Python
# attributes can be removed with a function
u.remove_attr('name')
```

### Sub-Entries

Entries can itself contain other sub-entries. This is useful to store hierarchical information and relations within data. Sub-entries can be accessed either via attribute-syntax, dictionary-syntax or directly from `._entries`

##### Adding Entries

```Python
u = unisens.Unisens('.')

# add subentry directly by giving it a parent link
signal1 = unisens.SignalEntry('signal1.bin', parent=u)

# or add a subentry later (e.g. to preserve a certain order in the XML)
signal2 = unisens.SignalEntry('signal2.bin', parent='.') # parent is the folder
u.add_entry(signal2)


```

##### Accessing Entries

```Python
# Sub-entries can be accessed via attributes, keys or indices
u.signal1_bin
u['signal1.bin']
u._entries[0]

# abbreviations are allowed
u.signal1
u['signal1']

# Sub-entries can be iterated
for entry in u:
    print(entry)
	# >> <signalEntry(signal1.bin)>
    # >> <signalEntry(signal2.bin)>


```

##### Removing Entries

```Python
# Subentries can be deleted by their id
u.remove_entry('signal1.bin')

# abbreviations are allowed here as well
u.remove_entry('signal2')
```

## Unisens

Unisens is the main object containing all other entries. It inherits from `Entry` and therefore shares all functionality declared at `Entry` below.

```Python
import unisens

u = unisens.Unisens('c:/unisens', makenew=True, autosave=True, readonly=False)
# makenew will force to create a new object, even if one exists
# autosave will update and save the XML on every miniscule change
# readonly = True would prevent the XML from updating
```

## SignalEntry

SignalEntries can be used to store continuous numeric data with high frequency, e.g. ECG signals. They are saved in binary or csv format. It is possible to save multiple channels. Things like sample frequency and other meta information can be saved in them as well. Data must be of size `[1, N]`.

```Python
from unisens import Unisens, SignalEntry

u = Unisens('c:/unisens', makenew=True, autosave=True, readonly=False)
sfreq = 256
signal = np.random.rand(2, sfreq*300) # 5 minutes of data
entry = SignalEntry(id='ECG.bin')
u.add_entry(entry) # must be called before setting data
entry.set_data(signal, sampleRate=sfreq, unit='mV', ch_names=['ECG I', 'ECG II'])

################
## alternatively

from unisens import Unisens, SignalEntry

u = Unisens('c:/unisens', makenew=True)
sfreq = 256
signal = np.random.rand(2, sfreq*300) # 5 minutes of data
SignalEntry(id='ECG.bin', parent=u).set_data(signal, sampleRate=sfreq)
u.save()
```

## ValuesEntry
`ValuesEntry` is used for low-frequency continuously sampled data, e.g. Temperature or RR intervals. It is basically equivalent to `SignalEntry` except that it saves data in CSV (text) format, and not binary. Data must be of size `[N, 1]`, i.e. column-wise, with indices in the first column. The integer indices are matched with the sample rate and the unisens timestamp start to display correctly in the Un isensViewer.

```Python
from unisens import Unisens, ValuesEntry

u = Unisens('c:/unisens', makenew=True, autosave=True)
temperature = np.random.randint(10, 40, [1, 300]) # 5 minutes of data
entry = ValuesEntry(id='temperature.csv')
u.add_entry(entry) # must be called before setting data
entry.set_data(temperature, sampleRate=1, unit='C')
```

## EventEntry

`EventEntry` is used for data that is not sampled continuously, but recorded on an event basis, e.g. 

```Python
from unisens import Unisens, EventEntry

u = Unisens('c:/unisens', makenew=True, autosave=True)
temperature = []
times = []
```


## CustomEntry

## CustomAttributes