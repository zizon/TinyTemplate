#!/usr/bin/env python
# -*- coding: utf8 -*-

import types
from tiny_template_engine import TinyRender
from tiny_template_engine import TinyTemplateEngine
from tiny_template_engine import TinyDataDriver

class TableGenerator(TinyDataDriver):
    
    def __init__(self,id=0):
        super(TableGenerator,self).__init__()
        self.indent = u'    '
        self.id = id 
        
    def table(self,header_group,rows,format):
        header,colors = self._header_row(header_group)
        body = self._table_row(rows,format,colors)

        return u'\n'.join([
                    u'<table>',
                    header,
                    body,
                    u'</table>'
        ])
    
    def _gen_name(self):
        self.id = self.id + 1
        return u'__bot_gen_%s__' % (self.id)
    
    def _table_row(self,datas,formats,colors):
        name = self._gen_name()
        basic_indent = 2
        indent = self.indent
        
        # bind data
        self.bind(name,datas)
       
        cols = []
        for i,format in enumerate(formats):
            format = format.replace(u'__VALUE__',
                    u'%s[row][%s]'%(name,i)
            )
            cols.append(u"%s<td class='color-group-%s' %s/>" % (
                indent*(basic_indent*2),
                colors[i],
                format, 
            ))
        
        rows = u'\n'.join([
            u"%s<tr tiny-repeat='len(%s)' tiny-repeat-index='row'>" % (
                (basic_indent+1) * indent ,
                name
            ),
            u'\n'.join(cols),
            u'%s</tr>'% ((basic_indent+1) * indent )
        ])
        return u'\n'.join([u'%s<tbody>' % (basic_indent * indent),rows,u'%s</tbody>' % (basic_indent*indent)])

    def _calculate_list_like(self,list_like):
        width = len(list_like)
        height = 1 if width > 0 else  0 
        max_height = height
        for _,child in list_like:
            if type(child) is types.ListType:
                # special case,
                # recursive calculate
                child_width,child_height = self._calculate_list_like(child)
                if child_width > 0:
                    width = width - 1 + child_width
                if child_height > 0:
                    if height  + child_height > max_height:
                        max_height = height  + child_height 
            elif child is not None:
                print child
                raise Exception(u'%s`s child should be None or List' % _ )
        return width,max_height
    
    def _calculate_colors(self,header):
        def copy_header(header):
            new_header = []
            for name,child in header:
                if child is None:
                    new_header.append([
                        name,
                        None,
                        -1
                    ])
                else:
                    new_header.append([
                        name,
                        copy_header(child),
                        -1
                    ])
            return new_header
        
        # mark numbers
        header = copy_header(header)
        pending = header
        index = 1
        while len(pending) > 0:
            new_pending = []
            for tuple in pending:
                tuple[2] = index
                index = index + 1
                if tuple[1] is not None:
                    new_pending.extend(tuple[1])
            pending = new_pending
        
        # extract colors 
        def extract(header):
            colors = []
            for name,child,color in header:
                if child is None:
                    colors.append(color)
                else:
                    colors.extend(extract(child))
            return colors
        
        return extract(header)
        
    def _header_row(self,header,color=0):
        width,height = self._calculate_list_like(header)
        rows = []
        
        indent = self.indent 
        basic_indent = 2
        process = header
        while len(process) > 0:
            # reset 
            next = [] 
            cols = []
            for name,child in process:
                color = color + 1
                if child is None:
                    cols.append(u"%s<td class='color-group-%s' %s>%s</td>" % 
                        (

                            indent*(2+basic_indent),
                            color,
                            u"rowspan='%s'" % height if height > 1 else u'',
                            name
                        )
                    )
                else:
                    sub_width,sub_height = self._calculate_list_like(child)
                    cols.append(u"%s<td class='color-group-%s' %s >%s</td>" % 
                            (
                                indent*(2+basic_indent),
                                color,
                                u"colspan='%s'" % sub_width if sub_width > 1 else u'' ,
                                name, 
                            )
                    )
                    next.extend(child)
            
            # build row
            rows.append(u'\n'.join([u'%s<tr>' % (indent *(1+basic_indent)) ,u'\n'.join(cols),u'%s</tr>' % (indent*(1+basic_indent))]))
            process = next 
            width,height = self._calculate_list_like(next)
            
        colors = self._calculate_colors(header)
        return u'\n'.join([u'%s<thead>' % (indent*basic_indent),u'\n'.join(rows),u'%s</thead>' % (indent*basic_indent)]),colors
    
    def _eval_tiny_bot(self,node,binding):
        attrs = node['__attrs__']
        name = node['__name__']
        
        # sanity check
        if name.lower() != 'table':
            raise Exception('tiny-bot only support <table> tag')
       
        # config 
        config = eval(attrs['tiny-bot'],binding)
        table = self.table(config['header'],config['data'],config['format']) 
        
        # parse
        root = TinyTemplateEngine(table).root
        
        # fix parent
        root['__parent__'] = node['__parent__']
        
        # clear attr
        del attrs['tiny-bot']
        
        return [root]

if __name__ == '__main__':
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
    
    print TinyRender().driver(bot).define('example.template').bind({
        'test_bot':{
            'header':header,
            'data':[[1,2,3,4],[5,6,7,8]],
            'format':formats
        },
        'data':[[1,2,3,4],[5,6,7,8]],
    }).render()


    print bot.table(header,[1,2,3,4],formats)
    print header
    print '----'
    print bot._calculate_list_like(header)
    print '----'
    page,colors = bot._header_row(header)
    print page
    print colors

