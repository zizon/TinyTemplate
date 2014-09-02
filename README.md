TinyTemplate
----
a tiny tempalte engine that generate and fills xml like files  
for example,given a template file,named 'example.template'  
```html
<table>
    <tr tiny-repeat='len(data)' tiny-repeat-index='row'>
        <td class='color-blue' tiny-data='data[row][0]'/>
        <td tiny-number='data[row][1]'/>
        <td tiny-percent='data[row][2]'/>
    </tr>
</table>
```
and style rule named 'example.style'  
```javascript
{
    "table":{
        "border":"dotted"
    },

    ".color-blue":{
        "color":"blue"
    }
}
```
with python code like  
```python
from tiny_template_engine import TinyRender
TinyRender().define('example.template').bind({
        'data':[
                [1,2,3,4],
                [5,6,7,8],
        ]
    }).render('example.style')
```
will output file like:  
```html
<table style='border:dotted;'>
    <tr >
        <td style='color:blue;'>1</td>
        <td >2</td>
        <td >300.00%</td>
    </tr>
    <tr >
        <td style='color:blue;'>5</td>
        <td >6</td>
        <td >700.00%</td>
    </tr>
</table>
```

Template Attribute Elements
----
- tiny-repeat  
  generate number of elements specified by evaluated value.  
  *tiny-repeat-index* provide a way to trake index of the evaluated elements.  

- tiny-number  
  render evalauted value to a 123,456.00 style.  
  use *tiny-force-integer* to force round fractional part.  
  use *tiny-color* whan one needs a positive number to be in red color and negetive value in green.  
  one can change the color styling by specify _tiny-positive-number_ and _tiny-negetive-number_ in style file.  

- tiny-data  
  fill content with evaluated raw string presentation.  

- tiny-percent  
  render numbers in percent format,like 87.53%.  
  default with color style similar to *tiny-color*.but can be disable with extra *tiny-default-color*  

Plugale Template Driver
----
One can extend the default *TineDataDriver* to add extra process property to this template engine.  

for example,this repo ships with a GenerateTable driver in *table_generato.py*, which provide a *tiny-bot* attribute to help generate table.  

by given tempalte:
```html
<table tiny-bot='test_bot'/> 
```
and python configuration
```python
bot = TableGenerator()
header = [
    ('header0',None),
    ('header1',[
        ('header2',None),
        ('header3',None),
    ]),
    ('header4',[('header5',None)]),
]
formats = [
    "tiny-number='__VALUE__'",
    "tiny-percent='__VALUE__'",
    "tiny-default-color='' tiny-percent='__VALUE__'",
    "tiny-force-integer='' tiny-number='__VALUE__'",
    ]

TinyRender().driver(bot).define('example.template').bind({
    'test_bot':{
        'header':header,
        'data':[[1,2,3,4],[5,6,7,8]],
        'format':formats
    },
}).render()
```
will generat table like 
```html
<table >
    <thead >
        <tr >
            <td rowspan='2' class='color-group-1'>header0</td>
            <td colspan='2' class='color-group-2'>header1</td>
            <td class='color-group-3'>header4</td>
        </tr>
        <tr >
            <td class='color-group-4'>header2</td>
            <td class='color-group-5'>header3</td>
            <td class='color-group-6'>header5</td>
        </tr>
    </thead>
    <tbody >
        <tr >
            <td class='color-group-1'>1</td>
            <td class='color-group-4 tiny-positive-number'>200.00%</td>
            <td class='color-group-5'>300.00%</td>
            <td class='color-group-6'>4</td>
        </tr>
        <tr >
            <td class='color-group-1'>5</td>
            <td class='color-group-4 tiny-positive-number'>600.00%</td>
            <td class='color-group-5'>700.00%</td>
            <td class='color-group-6'>8</td>
        </tr>
    </tbody>
</table>
```




