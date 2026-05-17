import os
import zipfile
import shutil
import re
import xml.etree.ElementTree as ET
from urllib.parse import unquote
from pathlib import Path


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff', '.tif'}
OPF_NS = {'opf': 'http://www.idpf.org/2007/opf'}
NCX_NS = {'ncx': 'http://www.daisy.org/z3986/2005/ncx/'}
CONTAINER_NS = {'container': 'urn:oasis:names:tc:opendocument:xmlns:container'}
FILTER_TITLES = {'书名页', '封面', '版权页', '扉页', '内容提要', '图书在版编目数据'}


class EpubParser:
    def __init__(self, epub_path, output_root):
        self.epub_path = epub_path
        self.epub_name = Path(epub_path).stem
        self.output_root = output_root
        self.output_dir = os.path.join(output_root, self.epub_name)
        self.image_dir = os.path.join(self.output_dir, 'image')
        self.temp_dir = os.path.join(self.output_dir, '_temp_extracted')
        self.opf_path = None
        self.opf_dir = None

    def parse(self):
        self._prepare_output_dirs()
        self._extract_epub()
        self._find_opf_path()
        self._extract_images()
        self._generate_toc_xml()
        self._cleanup_temp()
        print(f"解析完成！输出目录: {self.output_dir}")

    def _prepare_output_dirs(self):
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

    def _extract_epub(self):
        with zipfile.ZipFile(self.epub_path, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)

    def _find_opf_path(self):
        container_xml = os.path.join(self.temp_dir, 'META-INF', 'container.xml')
        if not os.path.exists(container_xml):
            for root, dirs, files in os.walk(self.temp_dir):
                for f in files:
                    if f.endswith('.opf'):
                        self.opf_path = os.path.join(root, f)
                        self.opf_dir = os.path.dirname(self.opf_path)
                        return
            raise FileNotFoundError("未找到OPF文件")

        tree = ET.parse(container_xml)
        root = tree.getroot()
        rootfile = root.find('.//container:rootfile', CONTAINER_NS)
        if rootfile is not None:
            opf_relative = rootfile.get('full-path')
            self.opf_path = os.path.join(self.temp_dir, opf_relative)
            self.opf_dir = os.path.dirname(self.opf_path)

    def _extract_images(self):
        for root, dirs, files in os.walk(self.temp_dir):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in IMAGE_EXTENSIONS:
                    src_path = os.path.join(root, file)
                    dest_path = os.path.join(self.image_dir, file)
                    counter = 1
                    while os.path.exists(dest_path):
                        name_stem = Path(file).stem
                        dest_path = os.path.join(self.image_dir, f"{name_stem}_{counter}{ext}")
                        counter += 1
                    shutil.copy2(src_path, dest_path)
                    print(f"提取图片: {file}")

    def _generate_toc_xml(self):
        toc_xml_path = os.path.join(self.output_dir, 'toc.xml')
        root = ET.Element('toc')
        root.set('epub_name', self.epub_name)

        opf_tree = ET.parse(self.opf_path)
        opf_root = opf_tree.getroot()

        manifest = opf_root.find('opf:manifest', OPF_NS)
        spine = opf_root.find('opf:spine', OPF_NS)

        id_to_href = {}
        if manifest is not None:
            for item in manifest.findall('opf:item', OPF_NS):
                item_id = item.get('id')
                href = item.get('href')
                id_to_href[item_id] = href

        toc_items = []
        if spine is not None:
            for itemref in spine.findall('opf:itemref', OPF_NS):
                item_id = itemref.get('idref')
                if item_id in id_to_href:
                    toc_items.append({
                        'id': item_id,
                        'href': id_to_href[item_id],
                        'title': self._extract_title_from_html(id_to_href[item_id])
                    })

        nav_toc = self._parse_nav_toc()
        if nav_toc:
            nav_toc = self._filter_toc_items(nav_toc)
            for nav_item in nav_toc:
                self._add_nav_to_xml(root, nav_item)
        else:
            for i, item in enumerate(toc_items, 1):
                chapter = ET.SubElement(root, 'chapter')
                chapter.set('order', str(i))
                chapter.set('id', item['id'])
                chapter.set('href', item['href'])
                title_elem = ET.SubElement(chapter, 'title')
                title_elem.text = item['title'] or item['href']

        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')
        tree.write(toc_xml_path, encoding='utf-8', xml_declaration=True)
        print(f"目录XML已生成: {toc_xml_path}")

    def _filter_toc_items(self, items):
        filtered = []
        for item in items:
            title = item.get('title', '')
            if title in FILTER_TITLES:
                continue
            if 'children' in item:
                item['children'] = self._filter_toc_items(item['children'])
            filtered.append(item)
        return filtered

    def _parse_nav_toc(self):
        toc_ncx_path = None
        nav_xhtml_path = None

        for root, dirs, files in os.walk(self.temp_dir):
            for f in files:
                if f.lower() == 'toc.ncx':
                    toc_ncx_path = os.path.join(root, f)
                elif f.lower().endswith('nav.xhtml') or f.lower() == 'nav.html':
                    nav_xhtml_path = os.path.join(root, f)

        if toc_ncx_path:
            return self._parse_ncx(toc_ncx_path)
        elif nav_xhtml_path:
            return self._parse_nav_xhtml(nav_xhtml_path)
        return None

    def _parse_ncx(self, ncx_path):
        tree = ET.parse(ncx_path)
        root = tree.getroot()
        nav_map = root.find('ncx:navMap', NCX_NS)
        if nav_map is None:
            return None
        return self._parse_nav_points(nav_map, NCX_NS, 'ncx')

    def _parse_nav_points(self, parent, ns, ns_prefix):
        items = []
        for nav_point in parent.findall(f'{ns_prefix}:navPoint', ns):
            item = {}
            nav_label = nav_point.find(f'{ns_prefix}:navLabel/{ns_prefix}:text', ns)
            if nav_label is not None and nav_label.text:
                item['title'] = nav_label.text.strip()

            content = nav_point.find(f'{ns_prefix}:content', ns)
            if content is not None:
                item['href'] = content.get('src', '')

            children = self._parse_nav_points(nav_point, ns, ns_prefix)
            if children:
                item['children'] = children

            if 'title' in item or 'href' in item:
                items.append(item)
        return items

    def _parse_nav_xhtml(self, nav_path):
        tree = ET.parse(nav_path)
        root = tree.getroot()
        for elem in root.iter():
            if 'nav' in elem.tag and elem.get('{http://www.idpf.org/2007/ops}type') == 'toc':
                ol = elem.find('.//{http://www.w3.org/1999/xhtml}ol')
                if ol is not None:
                    return self._parse_ol_items(ol)
        return None

    def _parse_ol_items(self, ol_element):
        items = []
        ns = '{http://www.w3.org/1999/xhtml}'
        for li in ol_element.findall(f'{ns}li'):
            item = {}
            a = li.find(f'{ns}a')
            if a is not None:
                item['href'] = a.get('href', '')
                if a.text:
                    item['title'] = a.text.strip()

            child_ol = li.find(f'{ns}ol')
            if child_ol is not None:
                children = self._parse_ol_items(child_ol)
                if children:
                    item['children'] = children

            if 'title' in item or 'href' in item:
                items.append(item)
        return items

    def _add_nav_to_xml(self, parent, nav_item, order=1):
        chapter = ET.SubElement(parent, 'chapter')
        chapter.set('order', str(order))
        if 'href' in nav_item:
            chapter.set('href', nav_item['href'])
        if 'id' in nav_item:
            chapter.set('id', nav_item['id'])

        title_elem = ET.SubElement(chapter, 'title')
        title_elem.text = nav_item.get('title', nav_item.get('href', ''))

        if 'children' in nav_item:
            children_elem = ET.SubElement(chapter, 'children')
            for i, child in enumerate(nav_item['children'], 1):
                self._add_nav_to_xml(children_elem, child, i)

    def _extract_title_from_html(self, href):
        href = unquote(href.split('#')[0])
        html_path = os.path.join(self.opf_dir, href)
        if not os.path.exists(html_path):
            return os.path.basename(href)

        try:
            with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE | re.DOTALL)
                if match:
                    return match.group(1).strip()
                match = re.search(r'<h[1-6][^>]*>([^<]+)</h[1-6]>', content, re.IGNORECASE | re.DOTALL)
                if match:
                    return match.group(1).strip()
        except:
            pass
        return os.path.basename(href)

    def _cleanup_temp(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
