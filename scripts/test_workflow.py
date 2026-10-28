#!/usr/bin/env python3
"""Offline behavioral checks; never contacts or publishes to external services."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import scrape_product as scrape
from content_plan import build_content_plan
from optimize_image import strip_metadata, compress, validate, create_transport_jpeg, inspect_metadata
from update_manifest import load_manifest, write_manifest, update_manifest, validate_post_url, SHEET_ID, SHEET_URL, IDENTITIES
from validate_campaign import validate_campaign, digest, validate_facebook, validate_linkedin, validate_transport
from validate_completion import expected_row, validate_completion

URL='https://www.igugehealthy.com/mushroom-coffee-12345.html'
HTML='''<button id="product-gallery-main"><img src="/hero.webp"><img class="brand-watermark-logo" src="/logo.webp"></button>
<div class="detail-copy"><h1>Mushroom Coffee Powder</h1>
<p class="lead">Coffee powder and mushroom blend for private label product discussions.</p>
<dl class="detail-quick-facts"><div><dt>Format</dt><dd>Powders</dd></div><div><dt>MOQ</dt><dd>500 boxes</dd></div></dl>
<table class="key-attributes-table"><tr><th>Dosage form</th><td>Powder</td></tr>
<tr><th>Main ingredient</th><td>Coffee powder, Mushroom blend</td></tr>
<tr><th>Service</th><td>Private label / OEM / ODM</td></tr><tr><th>MOQ</th><td>500 boxes</td></tr>
<tr><th>Function</th><td>GENERIC IMMUNITY CLAIM</td></tr><tr><th>Product benefit</th><td>GENERIC METABOLISM CLAIM</td></tr></table>
<button class="add-quote" data-id="10000"></button></div>
<div class="pc-overview-copy"><p>Mushroom Coffee Powder is available for private label discussions.</p><p class="pc-note">GENERIC DEVELOPMENT NOTE</p>
<dl class="pc-specs"><div><dt>Format</dt><dd>Powder</dd></div></dl></div>
<section class="pc-block pc-formula"><p class="pc-ingredient-reference">Coffee powder, Mushroom blend</p><p>GENERIC FORMULA DISCUSSION</p></section>
<section class="pc-block pc-packaging"><p>GENERIC PACKAGING OPTION</p></section>
<section class="pc-block pc-faq"><p>GENERIC FAQ CLAIM</p></section>'''


def parse(html):
    p=scrape.IGugeHTMLParser();p.raw_html=html;p.feed(html);p.close();return p


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
    def tearDown(self): self.temp.cleanup()
    def product(self):
        with patch.object(scrape,'fetch_html',return_value=parse(HTML)):
            return scrape.extract_product(URL)
    def campaign(self, mode='live'):
        product=self.product();plan=build_content_plan(product)
        from io import BytesIO
        b=BytesIO();Image.new('RGB',(1000,1000),'#b27672').save(b,'PNG')
        with patch.object(scrape,'fetch_bytes',return_value=(b.getvalue(),'image/png')):
            run=scrape.create_run(product,self.root,plan,mode)
        path=run/'manifest.json';m=load_manifest(path)
        fb='''☕ A powder format gives your team a clear starting point for product evaluation.
🍄 Coffee powder and a mushroom blend are listed as the main ingredients.
📦 The published minimum order quantity is five hundred boxes for this product.
✅ Private label, OEM and ODM services are listed for sourcing discussions.

Compare the product information with your brand brief. Confirm the complete formula, serving specification and preferred packaging during sample discussions. Bring your target market and estimated order quantity so the final specification can be agreed before ordering.

Contact iGuge healthy to discuss your product requirements.

'''+URL+'\n\n#Coffee #MushroomCoffee #Powder #PrivateLabel #Sourcing #OEM #ODM #ProductDevelopment'
        li='''Planning a coffee product for your brand begins with a clear sourcing brief. The published product information provides a starting point for discussing the format, ingredient direction and order requirements with the supplier.

- The product is presented in powder format.
- Coffee powder and a mushroom blend are listed as the main ingredients.
- The published minimum order quantity is five hundred boxes.
- Private label, OEM and ODM services are listed for discussion.

Use these details to prepare a sample brief that separates the listed product facts from choices still to be agreed. Ask for the complete ingredient declaration, serving specification and intended packaging. A mushroom blend description does not establish individual species or ingredient quantities, so those details should be confirmed for the selected formula. Record the agreed sample requirements and artwork before moving to an order.

Contact iGuge healthy with your target market, estimated quantity and preferred format. Discuss the proposed product specification and request the information your sourcing team needs to evaluate the next step.

'''+URL+'\n\n#Coffee #ProductDevelopment #PrivateLabel'
        Path(m['artifacts']['facebook_copy']).write_text(fb)
        Path(m['artifacts']['linkedin_copy']).write_text(li)
        im=Image.new('RGB',(1000,1000),'#c39988');enc,final,_=compress(strip_metadata(im),750*1024,(960,960))
        Path(m['artifacts']['social_image']).write_bytes(enc)
        create_transport_jpeg(final,Path(m['artifacts']['social_upload']))
        review={'product_url':URL,'source_review':'passed','copy_review':'passed','image_review':'passed',
                'claims':[{'claim':x,'quote':x} for x in ['Powder','Coffee powder, Mushroom blend','500 boxes','Private label / OEM / ODM']],
                'sha256':{k:digest(m['artifacts'][k]) for k in ['product_json','source_hero','facebook_copy','linkedin_copy','social_image','social_upload']}}
        write_manifest(Path(m['artifacts']['review']),review)
        return path,m
    def publish_fixture(self,path):
        # Synthetic local evidence only; fake links are never sent to a browser or service.
        for c in IDENTITIES:
            update_manifest(path,c,'pending',submission_started=True)
            ev=self.root/f'{c}.md';ev.write_text('OFFLINE TEST FIXTURE - no real publication')
            url='https://www.facebook.com/61595573086492/posts/offline-fixture' if c=='facebook' else 'https://www.linkedin.com/feed/update/urn:li:activity:123456/'
            update_manifest(path,c,'published',url=url,identity_id=IDENTITIES[c],evidence=ev)
        return load_manifest(path)
    def test_actual_template_extraction_and_source_boundaries(self):
        p=self.product()
        self.assertEqual(p['site_product_id'],'10000')
        self.assertEqual(p['model'],'')
        self.assertEqual(p['facts']['declared']['format'],'Powder')
        self.assertNotIn('GENERIC',p['product_detail_text'])
        self.assertNotIn('GENERIC',json.dumps(p['source_sections']))
        self.assertNotIn('function',p['facts']['declared'])
        self.assertNotIn('product_benefit',p['facts']['declared'])
        self.assertIn('GENERIC IMMUNITY',json.dumps(p['restricted_source_claims']))
        self.assertIn('GENERIC PACKAGING',json.dumps(p['discussion_sections']))
        self.assertFalse(p['facts']['conflicts'])
        self.assertEqual(p['hero_image_url'],scrape.BASE_URL+'/hero.webp')
    def test_format_synonym_is_not_a_conflict_or_corroboration(self):
        p=self.product()
        self.assertEqual(p['facts']['variations']['format']['selected_value'],'Powder')
        self.assertNotIn('format',p['facts']['corroborated'])
    def test_distinct_formats_and_order_units_remain_conflicts(self):
        for key,first,second in [('format','Powder','Capsule'),('moq','500 boxes','500 bottles'),('ingredients','Coffee, mushroom','Coffee, collagen')]:
            d,c,conf=scrape.extract_facts([(key,first)],[(key,second)],'')
            self.assertIn(key,conf)
            self.assertNotIn(key,d)
    def test_unrecognized_template_stops_instead_of_reselecting(self):
        with patch.object(scrape,'fetch_html',return_value=parse('<h1>Changed template</h1>')):
            with self.assertRaises(RuntimeError): scrape.extract_product(URL)
    def test_foreign_urls_and_non_product_canonicals_are_rejected(self):
        with self.assertRaises(ValueError): scrape.normalize_url('https://other.example/product-123.html')
        self.assertEqual(scrape.normalize_url(URL.replace('www.','')),URL)
        with patch.object(scrape,'fetch_html',return_value=parse('<link rel="canonical" href="/products/">'+HTML)):
            with self.assertRaises(RuntimeError): scrape.extract_product(URL)
    def test_other_facebook_page_permalink_rejected(self):
        with self.assertRaises(ValueError): validate_post_url('facebook','https://www.facebook.com/anotherpage/posts/123')
        self.assertTrue(validate_post_url('facebook','https://www.facebook.com/61595573086492/posts/123'))
    def test_linkedin_cannot_submit_before_facebook_verification(self):
        path,m=self.campaign()
        with self.assertRaises(ValueError): update_manifest(path,'linkedin','pending',submission_started=True)
        self.assertNotIn('publishing_started_at',load_manifest(path))
    def test_linkedin_share_permalink_and_company_guard(self):
        url='https://www.linkedin.com/feed/update/urn:li:share:123456?actorCompanyId=144048448'
        self.assertEqual(validate_post_url('linkedin',url),url)
        with self.assertRaises(ValueError): validate_post_url('linkedin',url.replace('144048448','999999'))
        with self.assertRaises(ValueError): validate_post_url('linkedin','https://www.linkedin.com/feed/update/urn:li:share:not-a-number')
    def test_skill_directory_cannot_be_output_root(self):
        with self.assertRaises(ValueError): scrape.resolve_output_root(str(Path(scrape.__file__).resolve().parents[1]/'runs'))
    def test_catalog_traverses_late_discovered_pagination_and_dedupes(self):
        def page(product,next_page):
            return parse(f'<div class="product-grid"><div class="product-card"><a href="/{product}-123.html">{product}</a></div></div><a href="{next_page}">next</a><a href="/news.html">news</a>')
        pages={scrape.PRODUCTS_URL:page('one','/products/2.html'),scrape.BASE_URL+'/products/2.html':page('two','/products/3.html'),scrape.BASE_URL+'/products/3.html':page('one','/products/index.html')}
        audit={}
        with patch.object(scrape,'fetch_html',side_effect=lambda u:pages[u]): pool=scrape.discover_candidates(audit)
        self.assertEqual(audit['page_count'],3);self.assertEqual(len(pool),2)
        self.assertFalse(any('news.html' in x['url'] for x in pool))
    def test_full_social_batch_needs_no_article(self):
        path,m=self.campaign();result=validate_campaign(m)
        self.assertEqual(result['status'],'validated');self.assertEqual(set(m['channels']),{'facebook','linkedin'})
    def test_stale_copy_blocks_submission(self):
        path,m=self.campaign();Path(m['artifacts']['facebook_copy']).write_text('Changed unreviewed text')
        with self.assertRaises(ValueError): update_manifest(path,'facebook','pending',submission_started=True)
        self.assertNotIn('publishing_started_at',load_manifest(path))
    def test_dry_run_cannot_publish(self):
        path,m=self.campaign('dry-run')
        with self.assertRaises(ValueError): update_manifest(path,'facebook','pending',submission_started=True)
    def test_wrong_identity_and_dashboard_are_rejected(self):
        path,m=self.campaign();update_manifest(path,'facebook','pending',submission_started=True)
        ev=self.root/'ev';ev.write_text('fixture')
        with self.assertRaises(ValueError): update_manifest(path,'facebook','published',url='https://www.facebook.com/61595573086492/posts/x',identity_id='wrong',evidence=ev)
        with self.assertRaises(ValueError): update_manifest(path,'facebook','published',url='https://www.facebook.com/profile.php?id=61595573086492',identity_id=IDENTITIES['facebook'],evidence=ev)
    def test_uncertain_submit_permanently_prevents_reselection(self):
        path,m=self.campaign();update_manifest(path,'facebook','pending',submission_started=True)
        update_manifest(path,'facebook','blocked',error='uncertain')
        m=load_manifest(path)
        self.assertTrue(m['channels']['facebook']['submission_started_at'])
        with self.assertRaises(ValueError): scrape.ensure_unsubmitted(m)
    def test_published_channel_cannot_be_reset(self):
        path,m=self.campaign();self.publish_fixture(path)
        with self.assertRaises(ValueError): update_manifest(path,'facebook','pending')
    def test_sheet_is_required_and_must_match_readback(self):
        path,m=self.campaign();m=self.publish_fixture(path)
        with self.assertRaises(ValueError): validate_completion(m)
        values=expected_row(m);vf=self.root/'values.json';write_manifest(vf,values)
        ev=self.root/'readback.json';write_manifest(ev,{'spreadsheet_id':SHEET_ID,'row':7,'values':values,'matching_rows':2})
        with self.assertRaises(ValueError): update_manifest(path,'google_sheet','reported',url=SHEET_URL,external_id=7,evidence=ev,values_file=vf)
        write_manifest(ev,{'spreadsheet_id':SHEET_ID,'row':7,'values':values,'matching_rows':1})
        update_manifest(path,'google_sheet','reported',url=SHEET_URL,external_id=7,evidence=ev,values_file=vf)
        Path(m['artifacts']['social_upload']).unlink()
        self.assertEqual(validate_completion(load_manifest(path))['status'],'complete')
        self.assertEqual(expected_row(load_manifest(path)),values)
    def test_candidate_budget_and_no_reuse(self):
        log_path,log=scrape.new_selection(self.root,targeted=False);log['mode']='dry-run'
        candidates=[{'url':f'https://www.igugehealthy.com/p{i}-123.html'} for i in range(20)]
        with patch.object(scrape,'extract_product',side_effect=ValueError('bad source')) as extract:
            with self.assertRaises(RuntimeError): scrape.select_candidate(candidates,self.root,log_path,log)
            self.assertEqual(extract.call_count,10)
        self.assertEqual(len(log['attempts']),10)
    def test_network_failure_stops_after_one_candidate(self):
        log_path,log=scrape.new_selection(self.root,targeted=False);log['mode']='dry-run'
        with patch.object(scrape,'extract_product',side_effect=RuntimeError('network unavailable')) as extract:
            with self.assertRaises(RuntimeError): scrape.select_candidate([{'url':URL},{'url':URL+'x'}],self.root,log_path,log)
            self.assertEqual(extract.call_count,1)
        self.assertEqual(log['status'],'blocked')
    def test_small_image_fails_and_metadata_is_removed(self):
        with self.assertRaises(ValueError): compress(Image.new('RGB',(100,100)),750*1024,(960,960))
        image=Image.new('RGB',(1000,1000));image.info.update(exif=b'fixture',icc_profile=b'fixture',xmp=b'fixture')
        clean=strip_metadata(image);self.assertFalse(clean.info)
        enc,_,_=compress(clean,750*1024,(960,960));p=self.root/'image.webp';p.write_bytes(enc)
        self.assertTrue(validate(p,'social',750*1024)['metadata_removed'])

    def test_original_social_copy_format_is_required(self):
        path,m=self.campaign()
        fb=Path(m['artifacts']['facebook_copy']).read_text()
        li=Path(m['artifacts']['linkedin_copy']).read_text()
        self.assertEqual(validate_facebook(fb,URL)['feature_lines'],4)
        self.assertEqual(validate_linkedin(li,URL)['feature_bullets'],4)
        with self.assertRaisesRegex(ValueError,'emoji feature lines'):
            validate_facebook(fb.replace('☕ ','',1),URL)
        with self.assertRaisesRegex(ValueError,'hashtags'):
            validate_facebook(fb.replace('#Coffee ','',1),URL)
        with self.assertRaisesRegex(ValueError,'feature bullets'):
            validate_linkedin(li.replace('- ',''),URL)

    def test_unknown_jpeg_application_metadata_is_rejected(self):
        p=self.root/'upload.jpg'
        create_transport_jpeg(strip_metadata(Image.new('RGB',(1000,1000))),p)
        self.assertTrue(inspect_metadata(p)['metadata_removed'])
        raw=p.read_bytes();payload=b'non-image application fixture'
        p.write_bytes(raw[:2]+b'\xff\xeb'+(len(payload)+2).to_bytes(2,'big')+payload+raw[2:])
        self.assertIn('APP11',inspect_metadata(p)['embedded_metadata'])
        with self.assertRaisesRegex(ValueError,'metadata'):
            validate_transport(p)

if __name__=='__main__': unittest.main(verbosity=2)
