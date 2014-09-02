#!/usr/bin/env python
# -*- coding: utf8 -*-

import codecs
import xml.sax
import json
import copy
import logging
import math
import atexit
import tarfile
from datetime import datetime
from xml.sax.handler import ContentHandler 

class IO(object):
    def __init__(self):
        self.defers = []
        atexit.register(lambda defers:map(lambda x:x(),defers),self.defers)
    
    def read(self,name,encoding=u'utf8'):
        file = codecs.open(name,u'r',encoding)
        content = file.read()
        file.close()
        return content
    
    def tempdir(self):
        # temp dir
        dir = None

        # try shmfs
        shmfs = u'/dev/shm'
        if os.path.exists(shmfs):
            dir = tempfile.mkdtemp(dir=shmfs)
        else:    
            dir = tempfile.mkdtemp()
        
        # defer cleanup
        self.defers.append(
            (lambda name:
                lambda :shutil.rmtree(name))
            (dir)
        )
        
        return dir
    
    def snapshot(self,content,name=None,encoding=u'utf8',compress=False):
        dir = self.tempdir()
        
        # make file 
        file_name = None 
        if name is not None:
            file_name = name
        else: 
            file_name = str(content.__hash__())
        
        # final path
        full_path = os.path.join(dir,file_name)
        
        # do write
        temp_file = codecs.open(full_path,u'w',encoding)
        temp_file.write(content)
        temp_file.close()
        
        if compress:
            compress_path = os.path.join(dir,u'%s.tar.bz2' % file_name)
            compress_out = tarfile.open(compress_path,u'w:bz2') 
            compress_out.add(full_path,file_name)
            compress_out.close()
            full_path = compress_path

        return full_path

class Node(object):
    def __init__(self,name=u'__root__',parent=None):
        self.node = {
            u'__name__':name,
            u'__content__':[],
            u'__attrs__':{},
            u'__parent__': parent,
            u'__children__':[],
        }

    def clone(self):
        # a shadow copy first
        copyed = Node(self[u'__name__'],self[u'__parent__'])

        # copy content
        copyed[u'__content__'] = list(self[u'__content__'])

        # copy attrs
        copyed[u'__attrs__'] = dict(self[u'__attrs__'])

        # copy children
        copyed[u'__children__'] = map(lambda child:child.clone(),self[u'__children__'])
        
        # fix parent
        for child in copyed[u'__children__']:
            child[u'__parent__'] = copyed

        return copyed

    def __str__(self):
        return self.node.__str__()
    
    def __getitem__(self,name):
        return self.node[name]
    
    def __setitem__(self,name,value):
        self.node[name] = value
        return
    
    def __delitem__(self,name):
        del self.node[name]
        return

class TinyStyleEngine(object):
    def __init__(self,name):
        self.styles = json.loads(IO().read(name))
    
    def style(self,name):
        return self.styles.get(name,{})
    
    def apply(self,node):
        # duplicate
        node_name = node[u'__name__']
        styles = {}
        
        # if any elemnt level style?
        styles.update(self.style(node_name))
        
        # if any class specified?
        attrs = node[u'__attrs__']
        if u'class' in attrs:
            for class_name in filter(lambda x:len(x) > 0 ,attrs[u'class'].split(u' ')):
                styles.update(self.style(u'.%s' % class_name))
            del attrs[u'class']

        # filter emtpy
        if u'' in styles:
            del styles[u'']
        
        if len(styles) > 0:
            # had style prestend?
            if u'style' in attrs:
                # reconstruct style
                for single_style in [ each.strip() for each in attrs['style'].split(u';')]:
                    single_style = single_style.split(u':')
                    style_name,style_value = single_style[0].strip(),u':'.join(single_style[1:]).strip()
                    if len(style_name) > 0:
                        styles[style_name] = style_value
            
            # build style string
            attrs[u'style'] = u''.join([ u'%s:%s;' % (key,value) for key,value in  styles.items()])
        
        return node
    
    def decorate(self,root):
        root = self.apply(root)
        for node in root[u'__children__']:
            self.apply(node)
            node[u'__children__'] = map(lambda x:self.decorate(x),node[u'__children__'])
        return root

class TinyTemplateEngine(ContentHandler):
    
    def __init__(self,template):
        xml.sax.parseString(template.encode(u'utf8'),self)
    
    def startDocument(self):
        # document root dom nodes
        self.root = Node()

        # current dom node infos
        self.current_node = self.root 
        
    def startElement(self,name,attrs):
        # current container 
        parent = self.current_node 
        node = Node(name,parent) 
        
        # attach to parent 
        parent[u'__children__'].append(node)
            
        # parent has content?
        parent[u'__content__'].append(u'__node__')
        
        # attach attributes
        node_attrs = node[u'__attrs__'] 
        for attr in attrs.getNames():
            node_attrs[attr] = attrs.getValue(attr)

        # update current node
        self.current_node = node
    
    def endElement(self,name):
        # update current node
        parent = self.current_node[u'__parent__']
        if parent is None:
            # a root node
            self.root[u'__children__'].append(self.current_node)
            self.current_node = None
        else:
            self.current_node = parent 
    
    def characters(self,content):
        if self.current_node is None:
            # no node associate with,drop it
            return
        self.current_node[u'__content__'].append(content)

class TinyRender(object):
    
    def __init__(self):
        self._driver = TinyDataDriver()
    
    def driver(self,driver):
        self._driver = driver
        return self

    def define(self,template):
        self.root = TinyTemplateEngine(IO().read(template)).root
        return self
    
    def bind(self,binding):
        self._driver.evaluate(self.root,binding)
        return self
  
    def render(self,style=None):
        if style is not None:
            self.root = TinyStyleEngine(style).decorate(self.root)
        return  self.render_node(self.root)

    def render_node(self,node):
        name = node[u'__name__']
        
        # special case for root node
        if name == u'__root__':
            return u''.join(map(lambda x:self.render_node(x),node[u'__children__']))
        
        # now ,all node has a not none parent
        
        # build attrs
        attrs =u' '.join([ u"%s='%s'" % (key,value) for key,value in node[u'__attrs__'].items()])
        
        # build content
        # be care about node content
        content = []
        children = node[u'__children__']
        node_index = 0
        
        # for pretify reason,insert \n when meeting congigous __node__ content
        meet_node = False
        indention = None
        for part in node[u'__content__']:
            if part != u'__node__':
                meet_node = False
                content.append(part)
            else:
                if meet_node:
                    # got the right indention,do nothing
                    content.append(indention)
                else:
                    # find indention
                    space = 0
                    done = False

                    # backtrack the content to find idention
                    for content_index in range(len(content)-1,-1,-1):
                        current = content[content_index]
                        for char in range(len(current)-1,-1,-1):
                            char = current[char]
                            if char == u'\n' or char == u'>':
                                done = True
                                break
                            elif char == u' ':
                                space = space + 1
                            else:
                                # consider a intended inline,give up indention pretify
                                done = True
                                break
                                raise Exception(u'should be space or carier return,context:%s' % current)
                        if done:
                            break
                    indention = u'\n%s' % u''.join([u' ' for i in range(space)])
                    meet_node = True
                # special process for node
                content.append(self.render_node(children[node_index]))
                node_index = node_index + 1
        content = ''.join(content)

        return u'<%s %s>%s</%s>' % (
            name,
            attrs,
            content,
            name,
        )

class TinyDataDriver(object):
    def __init__(self):
        self.binding = {}
        
        magic_prefix = u'_eval_'
        self.evaluator = {}
        for attr in dir(self):
            # magic find
            if attr.startswith(magic_prefix):
                self.evaluator[attr[len(magic_prefix):].replace(u'_',u'-')] = getattr(self,attr)

    def bind(self,name,value):
        self.binding[name] = value
   
    def priority_attrs(self,attrs):
        # copy
        attrs = dict(attrs)
        
        # priority process order
        priority = []
        if u'tiny-repeat' in attrs:
            priority.append(u'tiny-repeat')
            del attrs[u'tiny-repeat']
        
        return priority + attrs.keys()

    def evaluate(self,node,binding=None):
        if node[u'__name__'] == u'__root__':
            map(lambda x:self.evaluate_node(x,binding),node[u'__children__'])
        else:
            raise Exception(u'not a root node,evaluate illege')
    
    def evaluate_node(self,node,binding=None):
        # node should had parent 
        if binding is not None:
            self.binding.update(binding)
        binding = self.binding
        
        # save parent
        parent = node[u'__parent__']
        brothers = parent[u'__children__']
        contents = parent[u'__content__']
        name = node[u'__name__']
        
        # find brother index
        brother_match = -1
        for i,brother in enumerate(brothers):
            if brother == node :
               brother_match = i
               break
        
        if brother_match == -1:
            raise Exception(u'no match node in parent, illege evaluate')
         
        # find content index
        content_match = -1
        content_meet = 0
        for i,content in enumerate(contents):
            if content == u'__node__':
                content_meet = content_meet + 1
                if content_meet == brother_match+1:
                    content_match = i
                    break
        
        if content_match == -1:
            raise Exception(u'no match content in parent for node content, illege evaluate')
        
        def replace_in_parent(content_match,brother_match,nodes):
            for i,node in enumerate(nodes):
                brothers.insert( i + brother_match,node )
                contents.insert( i + content_match,u'__node__' )
            # remove original
            total_nodes = len(nodes)
            brothers.pop(total_nodes+brother_match)
            contents.pop(total_nodes+content_match)
        
        # evaluated container 
        nodes = [node]
        
        # find evalutior for name
        evaluator = self.evaluator.get(name,None) 
        if evaluator is not None:
            nodes = evaluator(node,binding)
            # replace
            replace_in_parent(content_match,brother_match,nodes)
        
        # now,new nodes are associalted with main tree
        
        # mark node numbers
        total_nodes = len(nodes) 
        
        # index trackers
        # as attrs may generate more nodes also
        content_index_tracker = content_match
        brother_index_tracker = brother_match
        
        # deal with attrs
        for i,node in enumerate(nodes):
            # evaluate attr
            attrs = node[u'__attrs__']
            
            # new nodes may be generated by attr evaluator,
            # defer it.
            # or it will have trouble with tree organization
            for attr in self.priority_attrs(attrs):
                evaluator = self.evaluator.get(attr,None)
                if evaluator is not None:
                    # evaluate
                    evaluated = evaluator(node,binding)
                    
                    # replace `this` node
                    # attach to main tree
                    replace_in_parent(content_index_tracker,brother_index_tracker,evaluated)                    
                    # delegate evalution of new evaluated nodes
                    map(lambda x:self.evaluate_node(x,binding),evaluated)
                    
                    # hand out control already
                    # stop processing
                    return
            
            # here,means node not changed in main tree,
            # process children
            for child in node[u'__children__']:
                self.evaluate_node(child,binding)
    
    def _eval_tiny_repeat(self,node,binding):
        attrs = node[u'__attrs__']
        times = eval(attrs[u'tiny-repeat'],binding)
        index_name = attrs[u'tiny-repeat-index']
            
        # clear instrument
        del attrs[u'tiny-repeat']
        del attrs[u'tiny-repeat-index']
        
        # node parent
        parent = node[u'__parent__']
        
        # expand content
        repeated = []
        
        # reuse bindng context
        conflict = None
        if index_name in binding:
            conflict = binding[index_name]
        
        # generate
        for i in range(times):
            # bind index value
            binding[index_name] = i
            
            # DO copy
            # take care of recursive bind
            copyed = node.clone()

            # node not in parents acctualy,
            # so a direct evaluate_node will fail.
            # make a isolated container for this node,
            # then evalute/evaluate_node will work as expected.
            # this is a little wired.
            psuedo_root = Node()
            psuedo_root[u'__children__'].append(copyed)
            psuedo_root[u'__content__'].append(u'__node__')
            copyed[u'__parent__'] = psuedo_root
            self.evaluate(psuedo_root,binding)

            # node is evaluated
            # reaper nodes
            # re-associate parent 
            for child in psuedo_root[u'__children__']:
                child[u'__parent__'] = parent 
            
            repeated.extend(psuedo_root[u'__children__'])
        
        # recover conflict
        if conflict is not None:
            binding[index_name] = conflict
        
        return repeated
    
    def _eval_tiny_number(self,node,binding):
        attrs = node[u'__attrs__']
        
        # evaluate
        value = float(eval(attrs[u'tiny-number'],binding))
            
        # clear instrument
        del attrs[u'tiny-number']
        
        if u'tiny-force-integer' in attrs:
            # froce integer
            del attrs[u'tiny-force-integer']
            if not math.isnan(value):
                node[u'__content__'].append(u'{:,}'.format(int(value)))
            else:
                node[u'__content__'].append(u'{:,}'.format(0))
        else: 
            # fill content
            if math.isnan(value):
                node[u'__content__'].append(u'N/A')
            elif value == int(value): 
                node[u'__content__'].append(u'{:,}'.format(int(value)))
            else:
                node[u'__content__'].append(u'{:,.2f}'.format(value))
        
        if u'tiny-color' in attrs and not math.isnan(value):
            del attrs[u'tiny-color']
            css = u''
            # add class
            if u'class' in attrs:
                css = attrs[u'class']
            if value > 0:
                attrs[u'class'] = u'%s tiny-positive-number' % css 
            elif value < 0:
                attrs[u'class'] = u'%s tiny-negetive-number' % css 
     
        return [node]
    
    def _eval_tiny_percent(self,node,binding):
        attrs = node[u'__attrs__']
        # evaluate
        value = float(eval(attrs[u'tiny-percent'],binding))
        
        # clear instrument
        del attrs[u'tiny-percent']
        
        if not math.isnan(value):
            if u'tiny-precision' in attrs:
                format = u'{:,.%s%%}' % eval(attrs[u'tiny-precision'],binding)
                node[u'__content__'].append(format.format(value))
            else:
                node[u'__content__'].append(u'{:,.2%}'.format(value))
        else:
            node[u'__content__'].append(u'N/A')

        if u'tiny-default-color' not in attrs:
            css = u'' 
            # add class
            if u'class' in attrs:
                css = attrs[u'class']
            if value > 0:
                attrs[u'class'] = u'%s tiny-positive-number' % css 
            elif value < 0:
                attrs[u'class'] = u'%s tiny-negetive-number' % css 
        else:
            del attrs[u'tiny-default-color']

        return [node]

    def _eval_tiny_data(self,node,binding):
        attrs = node[u'__attrs__']
        node[u'__content__'].append(u'%s' % eval(attrs[u'tiny-data'],binding))
        
        # clear instrument
        del attrs[u'tiny-data']

        return [node] 
    
    def _eval_tiny_color_group(self,node,binding):
        attrs = node[u'__attrs__']
        css = u'tiny-color-group-%s' % eval(attrs[u'tiny-color-group'],binding)
         
        # attach css
        if u'class' in attrs:
            attrs[u'class'] = u'%s %s' % (attrs[u'class'],css)
        else:
            attrs[u'class'] = css
        
        # clear instrument
        del attrs[u'tiny-color-group']

        return [node]
