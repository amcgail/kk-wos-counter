from knowknow import *






from csv import DictReader
# This cell ensures there are not overflow errors while importing large CSVs

import sys
import csv
maxInt = sys.maxsize

while True:
    # decrease the maxInt value by factor 10
    # as long as the OverflowError occurs.

    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt/10)






        


class wos_counter:
    
    def __init__(
        self, 
        wos_txt_base, output_database, name_blacklist=[], 
            RUN_EVERYTHING=True, 
            groups=None, group_reps=None,
            citations_filter=None, journals_filter=None, debug=False, 
            trimCounters = False
    ):
        
        self.wos_txt_base = Path(wos_txt_base)
        assert(self.wos_txt_base.exists())
        
        self.name_blacklist = name_blacklist
        self.debug = debug
        self.output_database = output_database
        self.groups = groups
        self.group_reps = group_reps
        
        self.RUN_EVERYTHING = RUN_EVERYTHING
        self.citations_filter = citations_filter
        self.journals_filter = journals_filter
        self.trimCounters = trimCounters
        
        
        
        # Instantiating counters
        self.ind = defaultdict(lambda:defaultdict(int))
        self.track_doc = defaultdict(lambda:defaultdict(set))
        self.doc = defaultdict(lambda:defaultdict(int))


        
        
        
    
    def count_cocitations(self):
        
        allowed_refs = Counter(dict(self.doc['c'].items())).most_common(1000)
        allowed_refs = set( x[0] for x in allowed_refs )

        print("# allowed references for cocitation analysis: %s" % len(allowed_refs))
        print("Examples: %s" % str(list(allowed_refs)[:3]))
        
        refcount = 0
        
        for doc in self.doc_iterator():
            refs = list(doc.generate_references())
            for ref1 in refs:
                if ref1.full_ref not in allowed_refs:
                    continue
                    
                for ref2 in refs:
                    if ref2.full_ref not in allowed_refs:
                        continue
                    if ref1.full_ref >= ref2.full_ref:
                        continue

                    self.cnt((ref1.full_ref,ref2.full_ref), 'c1.c2', doc.uid)
                    self.cnt((ref1.publish,ref2.publish), 'c1y.c2y', doc.uid)

                    refcount += 1
                    if refcount % 10000 == 0:
                        print("%s cocitations logged" % refcount)

        print("Finished cocitation logging!")
        
        


            
        
    def cnt(self, term, space, doc):
        if ".".join(sorted(space.split("."))) != space:
            raise Exception(space, "should be sorted...")

        # it's a set, yo
        self.track_doc[space][term].add(doc)
        # update cnt_doc
        self.doc[space][term] = len(self.track_doc[space][term])
        # update ind count
        self.ind[space][term] += 1


        
    def doc_iterator(self):
        # processes WoS txt output files one by one, counting relevant cooccurrences as it goes
        self.dcount=0
        files = list(self.wos_txt_base.glob("**/*.txt"))
        for i, f in enumerate( files ):

            with f.open(encoding='utf8', newline='') as pfile:
                r = DictReader(pfile, delimiter='\t', quoting=3)
                rows = list(r)

            if i % 50 == 0:
                print("File %s/%s: %s" % (i, len(files),f.name))
                print("Document: %s" % self.dcount)
                print("Citations: %s" % len(self.doc['c']))
            
            if i > 10:
                if self.debug:
                    break

            for i, r in enumerate(rows):
                
                if r['DT'] != "Article":
                    continue
                                
                try:
                    int(r['PY'])
                except ValueError:
                    print(r)
                    raise

                # REMEMBER THIS! journals are in lowercase... not case sensitive
                
                # implements the journals filter!
                if self.journals_filter is not None and r['SO'].lower() not in self.journals_filter:
                    continue
        
                yield wos_doc(r)
                
                self.dcount+=1

    def count_citation(self, doc, ref):
        
        full_ref = ref.full_ref
        
        # implement grouping of references
        if self.groups is not None:
            if full_ref in self.groups:
                # retrieves retrospectively-computed groups
                full_ref = self.group_reps[
                    self.groups[full_ref]
                ]
            else:
                raise Exception('not in group...', full_ref)

        ref.full_ref = full_ref
        
        self.cnt(doc.journal, 'fj', doc.uid)
        self.cnt(doc.publish, 'fy', doc.uid)
        self.cnt(ref.publish, 'ty', doc.uid)
        self.cnt((ref.full_ref, doc.publish), 'c.fy', doc.uid)
        self.cnt((ref.full_ref, doc.journal), 'c.fj', doc.uid)

        self.cnt((doc.journal, doc.publish), 'fj.fy', doc.uid)

        self.cnt(ref.full_ref, 'c', doc.uid)
        
        if self.RUN_EVERYTHING:
            
            self.cnt((doc.publish, ref.publish), 'fy.ty', doc.uid)
            self.cnt((doc.journal, ref.publish), 'fj.ty', doc.uid)
                    
            self.cnt(ref.author, 'ta', doc.uid)
            self.cnt((doc.publish,ref.author), 'fy.ta', doc.uid)
            self.cnt((doc.journal,ref.author), 'fj.ta', doc.uid)
            
            self.cnt((ref.full_ref, doc.journal, doc.publish), 'c.fj.fy', doc.uid)
            
            # first author!
            ffa = doc.citing_authors[0]
            self.cnt(ffa, 'ffa', doc.uid)
            self.cnt((ffa,doc.publish), 'ffa.fy', doc.uid)
            self.cnt((ffa,doc.journal), 'ffa.fj', doc.uid)
            self.cnt((ref.full_ref,ffa), 'c.ffa', doc.uid)
            #self.cnt((ffa,r['SO'], int(r['PY'])), 'ffa.fj.fy', doc.uid)

            for a in doc.citing_authors:
                self.cnt(a, 'fa', doc.uid)
                self.cnt((a, doc.publish), 'fa.fy', doc.uid)
                self.cnt((a, doc.journal), 'fa.fj', doc.uid)
                #self.cnt((a,r['SO'], int(r['PY'])), 'fa.fj.fy', doc.uid)

                self.cnt((ref.full_ref,a), 'c.fa', doc.uid)

    def main_loop(self):
        
        for doc in self.doc_iterator():
            
            for ref in doc.generate_references():
                
                if ref.author in self.name_blacklist:
                    continue
                    
                if self.groups is not None and ref.full_ref not in self.groups:
                    continue
                
                self.count_citation(
                    doc,
                    ref
                )
    
    def save_counters(self):
        db = Dataset(self.output_database)
        db.clear_all()
        for k,count in self.doc.items():
            varname = "doc ___ %s" % k
            db.save_variable(varname, dict(count))

            
        for k,count in self.ind.items():
            varname = "ind ___ %s" % k
            db.save_variable(varname, dict(count))
    

    def count_ages(self):
        
        cbirthdays = defaultdict(lambda:2050)
        for (c,y),count in self.doc['c.fy'].items():
            if count == 0:
                continue
            cbirthdays[c] = min(cbirthdays[c], y)
            
        ffabirthdays = defaultdict(lambda:2050)
        for (c,y),count in self.doc['ffa.fy'].items():
            if count == 0:
                continue
            ffabirthdays[c] = min(ffabirthdays[c], y)

        tabirthdays = defaultdict(lambda:2050)
        for (y,c),count in self.doc['fy.ta'].items():
            if count == 0:
                continue
            tabirthdays[c] = min(tabirthdays[c], y)

        for doc in self.doc_iterator():

            refs = list(doc.generate_references())
            for i, ref in enumerate(refs):

                if ref.author in self.name_blacklist:
                    continue

                if self.groups is not None and ref.full_ref not in self.groups:
                    continue

                c = ref.full_ref
                ffa = doc.citing_authors[0]
                ta = ref.author

                # skips the hitherto uncounted
                if c not in self.doc['c'] or self.doc['c'][c] == 0:
                    continue
                if ffa not in self.doc['ffa'] or self.doc['ffa'][ffa] == 0:
                    continue
                if ta not in self.doc['ta'] or self.doc['ta'][ta] == 0:
                    continue

                cage1 = doc.publish - cbirthdays[c]
                ffaage1 = doc.publish - ffabirthdays[ffa]
                taage1 = doc.publish - tabirthdays[ta]

                if not all(x>=0 for x in [cage1,ffaage1,taage1]):
                    print(cage1, ffaage1, taage1)
                    print(self.doc['c'][ref.full_ref], self.doc['ffa'][doc.citing_authors[0]], self.doc['ta'][ref.author])
                    print(ref.full_ref, doc.citing_authors[0], ref.author)
                    print(cage1, ffaage1, taage1)
                    raise

                self.cnt((cage1,doc.journal), 'cAge.fj', doc.uid)

                self.cnt((cage1,doc.citing_authors[0]), 'cAge.ffa', doc.uid)
                for author in doc.citing_authors:
                    faage1 = doc.publish - ffabirthdays[author]
                    self.cnt((cage1,author), 'cAge.fa', doc.uid)
                    self.cnt(faage1, 'faAge', doc.uid)

                    self.cnt((faage1,ref.author), 'faAge.ta', doc.uid)
                    self.cnt((faage1,doc.publish,ref.author), 'faAge.fy.ta', doc.uid)
                    self.cnt((faage1,taage1), 'faAge.taAge', doc.uid)
                    self.cnt((cage1,faage1), 'cAge.faAge', doc.uid)

                    self.cnt((faage1,doc.publish), 'faAge.fy', doc.uid)

                self.cnt(ffaage1, 'ffaAge', doc.uid)

                self.cnt((ffaage1,ref.author), 'ffaAge.ta', doc.uid)
                self.cnt((ffaage1,doc.publish,ref.author), 'ffaAge.fy.ta', doc.uid)
                self.cnt((ffaage1,taage1), 'ffaAge.taAge', doc.uid)
                self.cnt((cage1,ffaage1), 'cAge.ffaAge', doc.uid)

                self.cnt((cage1,doc.publish), 'cAge.fy', doc.uid)
                self.cnt((doc.publish,taage1), 'fy.taAge', doc.uid)
                self.cnt((ffaage1,doc.publish), 'ffaAge.fy', doc.uid)

                for j, ref2 in enumerate(refs):
                    cage2 = doc.publish - cbirthdays[ref2.full_ref]
                    if i >= j:
                        continue

                    self.cnt((cage1, cage2), 'c1age.c2age', doc.uid)


    def run(self):
        self.main_loop()
        if self.RUN_EVERYTHING:
            self.count_ages()
            self.count_cocitations()
        self.save_counters()