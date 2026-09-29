import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from agent import merge,read_db,save
from review import apply_reviews
from run import report
import search_remoteok

class AgentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name); self.db=read_db(self.path)
        self.row={'source':'test','title':'Дизайнер карточек','url':'https://example.org/job/1','description':'Тестовая вакансия'}
        merge(self.db,[self.row]); self.id=self.db['jobs'][0]['id'];save(self.path/'jobs.json',self.db)
    def review(self,score=8):
        return {'job_id':self.id,'score':score,'reasoning':'Тестовая оценка','letter':'Тестовый отклик'}
    def test_duplicate_preserves_review(self):
        apply_reviews(self.path,[self.review()]); db=read_db(self.path)
        self.assertEqual(merge(db,[self.row]),0)
        self.assertEqual(len(db['jobs']),1)
        self.assertEqual(db['jobs'][0]['status'],'draft')
        self.assertEqual(db['jobs'][0]['score'],8)
    def test_threshold(self):
        apply_reviews(self.path,[self.review(7)])
        self.assertEqual(read_db(self.path)['jobs'][0]['status'],'new')
        self.assertFalse((self.path/'drafts').exists())
        apply_reviews(self.path,[self.review(8)])
        self.assertEqual(read_db(self.path)['jobs'][0]['status'],'draft')
    def test_no_overwrite(self):
        apply_reviews(self.path,[self.review()]); before=(self.path/'jobs.json').read_bytes()
        with self.assertRaises(ValueError):apply_reviews(self.path,[self.review()])
        self.assertEqual(before,(self.path/'jobs.json').read_bytes())
    def test_sent_not_redrafted(self):
        self.db['jobs'][0]['status']='sent';save(self.path/'jobs.json',self.db)
        with self.assertRaises(ValueError):apply_reviews(self.path,[self.review()])
    def test_invalid_batch_no_partial_draft(self):
        bad=self.review();bad['job_id']='missing'
        with self.assertRaises(ValueError):apply_reviews(self.path,[self.review(),bad])
        self.assertFalse((self.path/'drafts').exists())
        self.assertEqual(read_db(self.path)['jobs'][0]['status'],'new')
    def test_invalid_url_rejected(self):
        with self.assertRaises(ValueError):merge(self.db,[dict(self.row,url='javascript:alert(1)')])
    def test_source_failure_is_recorded(self):
        with patch.object(search_remoteok,'fetch',side_effect=OSError('Network unavailable')), patch.object(sys,'argv',['search_remoteok.py','--data-dir',str(self.path)]):
            with self.assertRaises(SystemExit) as ctx:search_remoteok.main()
        self.assertEqual(ctx.exception.code,1)
        self.assertIn('error',read_db(self.path)['runs'][-1])
        self.assertIn('Ошибка источника',report(self.path).read_text())

if __name__=='__main__':unittest.main()
