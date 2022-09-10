class Publication(models.Model):
    title= models.CharField(max_length=300, unique=True)
    document_id= models.CharField(max_length=300, default='empty', null=True)
    author_names= models.CharField(max_length=300, default='empty')
    author_ids= models.CharField(max_length=300, default='empty')
    DOCUMENT_TYPE_CHOICES= ('Article','Article'),('Conference Paper','Conference Paper'),\
                           ('Book Chapter','Book Chapter'),('Book','Book')
    document_type= models.CharField(max_length=100, choices=DOCUMENT_TYPE_CHOICES, default='empty')
    publication_name= models.CharField(max_length=300, default='empty')
    publisher= models.CharField(max_length=300, default='empty', null=True)
    cover_date= models.CharField(max_length=300, default='empty')
    cited_by= models.CharField(max_length=50, default='empty')
    scopus_document= models.BooleanField(default= True)

    def __str__(self):
        return self.title
      
      
class User(AbstractUser):
    username = models.CharField(_('username'), max_length = 200, unique = True )
    email = models.EmailField(_('email address'), unique = True)
    title = models.CharField(_('title'), max_length = 200, default = 'None' )
    department = models.CharField(_('department'), max_length = 200, default = 'None' )

    scopus_id= models.CharField(max_length=20, default='None')
    scopus_document_count = models.IntegerField(default=0)
    created_document_count = models.IntegerField(default=0)

    publications= models.ManyToManyField(Publication, through='Publication_listing')
    
    
class Publication_listing(models.Model):
    publication= models.ForeignKey(Publication, on_delete=models.CASCADE)
    author= models.ForeignKey(User, on_delete=models.CASCADE)
    page_range= models.CharField(max_length=50, default='none', null=True)
    deleted= models.BooleanField(default=False)

    def __str__(self):
        return self.publication.title

    class Meta:
        unique_together= [['publication','author']]
        
        
class Report(models.Model):
    report_year= models.CharField(max_length=150, default='None', null=True)
    article_count= models.IntegerField()
    conference_paper_count= models.IntegerField()
    book_chapter_count= models.IntegerField()
    book_count= models.IntegerField()
    citation_count= models.IntegerField()
    cited_by_count= models.IntegerField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.author.username + ' questionaire(' + str(self.created_at) + ')'        
