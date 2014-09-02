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
```html
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
```
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



