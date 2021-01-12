from knowknow import VariableNotFound

class SimpleStringGrouper:

    def __init__( self, dataset ):
        self.dataset = dataset

    def run(self):
        to_group = self.dataset.items('c')

        from itertools import groupby

        def gkey(k):
            ksp = k.split("|")
            if len(ksp) == 2:
                #return ksp[0] + "|" + ksp[1][:2] # first two letters!
                return ksp[0] + "|"
            else:
                return k

        provisional_groups = groupby(to_group, gkey)
        provisional_groups = [(x,list(y)) for x,y in provisional_groups]

        len(provisional_groups)

        skip_words = {'the','of','a','an','and'}

        def pair_matches(w1, w2):
            w1 = w1.lower().split("|")[1].split(" ")
            w2 = w2.lower().split("|")[1].split(" ")
            
            w1 = [x for x in w1 if x not in skip_words]
            w2 = [x for x in w2 if x not in skip_words]
            
            for i in range(min(len(w1),len(w2))):
                
                min_l = min(len(w1[i]),len(w2[i]))
                if w1[i][:min_l] != w2[i][:min_l]:
                    return False
                
            return True

        provisional_groups = [(x,y) for x,y in provisional_groups if len(y)>1]
            
        new_groups = {}
        new_group_reps = {}
        groupi = 0
            
        for k, vals in provisional_groups:
            
            for v1i, v1 in enumerate(vals):
                for v2i, v2 in enumerate(vals):
                    if v2i <= v1i:
                        continue
                        
                    if pair_matches(v1,v2):
                        if v1 in new_groups:
                            new_groups[v2] = new_groups[v1]
                        elif v2 in new_groups:
                            new_groups[v1] = new_groups[v2]
                        else:
                            new_groups[v1] = groupi
                            new_groups[v2] = groupi
                            groupi += 1
            
        # assign group representatives
        for g in range(groupi):
            new_group_reps[g] = max(
                [k for k,v in new_groups.items()
                if v == g],
                key=lambda x: self.dataset(c=x).cits
            )

        self.dataset.save_variable( 'groups', new_groups )
        self.dataset.save_variable( 'group_reps', new_group_reps )


class Grouper:
    def __init__( self, dataset ):
        self.dataset = dataset

        # the final variable we are constructing
        self.groups = {}
        
        # intermediate representation
        self.ft = {}



        try:
            self.ysum = self.dataset.load_variable("c.ysum")
            self.strings = list(self.ysum)
        except VariableNotFound:
            print("You need to generate ysum before running this notebook.")
            raise

        
    def traverse(self, x, gid):
        self.groups[x] = gid
        
        neighbors = self.ft[x]
        for n in neighbors:
            if n not in self.groups:
                self.traverse(n, gid)

    def run(self):

        from knowknow import pd, Counter, VariableNotFound
        from collections import defaultdict

        import string_grouper
        import editdistance


        # tracks the last group-id assigned
        new_gid = 0


        print(len(self.strings), 'strings total...')

        def isarticle(x):
            sp = x.split("|")
            if len(sp) < 2:
                return False
            
            try:
                int(sp[1])
                return True
            except ValueError:
                return False

        strings = [x for x in self.strings if '[no title captured]' not in x]
        articles = [x for x in strings if isarticle(x)]
        books = [x for x in strings if not isarticle(x)]

        print('sample articles:', articles[:10])
        print('sample books:', books[:10])
        print("%s articles, %s books to group" % (len(articles), len(books)))

        # grouping books

        # this cell may take quite a while to run.
        # on Intel i7-9700F this runs in about a minute on 185k names.

        self.books_grouped = string_grouper.match_strings(
            pd.Series(books), 
            number_of_processes=8, 
            min_similarity=0.7
        )

        # for books, we require that the authors are no more than 1 edit from each other
        # even after limiting the comparisons necessary, this takes about 20s on Intel i7-9700F

        
        self.ft = defaultdict(set)

        for i,r in self.books_grouped.iterrows():
            ls = r.left_side
            rs = r.right_side
            
            if ls == rs:
                continue
            
            la = ls.split("|")[0]
            ra = rs.split("|")[0]
            
            if editdistance.eval(la,ra) > 1:
                continue
            
            self.ft[ls].add(rs)
            self.ft[rs].add(ls)
            
        print("%s books have some connection to others in a group" % len(self.ft))

        # assigns group-ids based on the relational structure derived thus far
        # the code propagates ids through the network, assuming transitivity of equality
            
        for i,k in enumerate(books):
            if k in self.groups:
                continue
                
            self.traverse(k, new_gid)
            new_gid += 1

        print(len(set(self.groups.values())), 'groups total')
        print(Counter(gid for x,gid in self.groups.items() if len(x.split("|"))==2).most_common(10))

        # grouping articles

        # this cell may take quite a while to run.
        # on Intel i7-9700F this runs in five minutes on 234k entries.

        self.articles_grouped = string_grouper.match_strings(
            pd.Series(articles), 
            number_of_processes=8, # decrease this number to 1 or 2 for slower computers or laptops (the fan might start screaming)
            min_similarity=0.8 # the similarity cutoff is tighter for articles than for books
        )

        self.articles_grouped[(self.articles_grouped.similarity<1-1e-8)].sort_values("similarity")

        # for articles, we require that the entire citations is only 1 edit apart.
        # even after limiting the comparisons necessary, this takes about 20s on Intel i7-9700F

        # this cell produces the `ft` variable, which maps from each term to the set of terms equivalent. I.e., `ft[A] = {B1,B2,B3}`

        self.ft = defaultdict(set)

        for i,r in self.articles_grouped.iterrows():
            ls = r.left_side
            rs = r.right_side
            
            if ls == rs:
                continue
            
            la = ls.split("|")[0]
            ra = rs.split("|")[0]
                
            if editdistance.eval(ls,rs) > 2:
                continue
            
            self.ft[ls].add(rs)
            self.ft[rs].add(ls)
            #print(ls,"|||",rs)

        print("%s articles have some connection to others in a group" % len(self.ft))

        # assigns group-ids based on the relational structure derived thus far
        # the code propagates ids through the network, assuming transitivity of equality

        for i,k in enumerate(articles):
            if k in self.groups:
                continue
                
            self.traverse(k, new_gid)
            new_gid += 1

        # this line will break execution if there aren't as many groups assigned as we have articles and books
        assert( len(articles) + len(books) == len(self.groups) )

        print("%s books and %s articles total" % (len(books),len(articles)))

        from collections import defaultdict

        # saving the variable for later
        self.dataset.save_variable("groups", self.groups)
        self.dataset.save_variable("group_reps", self.get_reps())

        
    def get_reps(self):
        from collections import defaultdict
        ret = defaultdict(set)
        for k,v in self.groups.items():
            ret[v].add(k)
        ret = {
            k: max(v, key=lambda x:self.ysum[x]['total'])
            for k,v in ret.items()
        }
        return ret