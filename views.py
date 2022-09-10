from django.shortcuts import render, redirect, get_object_or_404, reverse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.template.defaultfilters import lower, upper
from pybliometrics.scopus import AuthorRetrieval, ScopusSearch, AbstractRetrieval, AffiliationSearch, \
    AffiliationRetrieval
from pybliometrics.scopus.utils import create_config, config
from pybliometrics.scopus import CitationOverview

from .forms import extMailForm, forgotPasswordForm, changePasswordForm, verifyPasswordForm, firsttimer_scopusid, \
    new_document_form, change_report_form
from .tokenhandler import send_activation_token, create_activation_token, send_reset_token, create_reset_token
from .models import Token
from .ldaphandler import ldapConnection
from django.urls import reverse
import logging

from datetime import datetime

from .models import User, Publication, Publication_listing, Report

# Create your views here.

#       code--site_search_bar
# statistics==publications
#     report==statistics


def index(request):
    """
    Index view
    """
    return render(request, 'accounts/index.html')

@login_required
def profile(request):

    keys= ['apikey','1']
    create_config(keys)

    my_user= request.user

    ## na to dw
    ##if my_user != kathigitis -> selida enimeroshs

    # if user has not set his scopus_id
    if request.user.scopus_id == 'None':
        print('outta here!')
        return firsttime_login(request)

    user_info= {
        'name': my_user.first_name + ' ' + my_user.last_name,
        'idiotita': my_user.title,
        'scopus_id': my_user.scopus_id
    }

    context= {'user_info': user_info}

    return render(request, 'accounts/profile1.html', context)

@login_required
def logoutView(request):
    logger.info('User %s has logged out' % request.user.username)
    logout(request)
    return render(request, 'accounts/byebye.html')

def forgotpassword(request):
    return HttpResponse('Forgot password view')

@login_required
def firsttime_login(request):

    # if user has already set his scopus_id
    # if request.user.scopus_id != 'None':
    #     print('outta here!')
    #     return main_page(request)


    my_user= request.user

    print('New User! Username: ' + my_user.username + '. Creating Account!')

    user_info= {
        'name': my_user.first_name + ' ' + my_user.last_name,
        'idiotita': my_user.title,
        'scopus_id': my_user.scopus_id
    }


    context= {'user_info': user_info}
    return render(request, 'accounts/first_timer1.html', context)

@login_required
def set_user(request):

    my_user= request.user

    my_user.scopus_id = request.GET.get('secret_key',False)
    my_user.save()

    author_creator(request)

    return main_page(request)

@login_required
def main_page(request):

    keys= ['1']
    create_config(keys)

    my_user= request.user

    # if user has not set his scopus_id
    if request.user.scopus_id == 'None':
        print('outta here!')
        return firsttime_login(request)

    user_info= {
        'name': my_user.first_name + ' ' + my_user.last_name,
        'idiotita': my_user.title,
        'scopus_id': my_user.scopus_id
    }

    context= {'user_info': user_info}

    return render(request, 'accounts/profile1.html', context)

@login_required
def author_creator(request):

    keys= ['1']
    create_config(keys)

    my_user= request.user

    #retrieves author data
    myUser_data = AuthorRetrieval(my_user.scopus_id)

    print(my_user.username + ' is registering!')

    myUser_documents= myUser_data.get_documents()

    for document in myUser_documents:
        # if this article exists in the database
        if Publication.objects.filter(title=document.title).exists() == True:
            # if the author is not listed on the article
            if Publication_listing.objects.filter(author=my_user,
                                                  publication__title=document.title).exists() == False:
                this_doc = Publication.objects.get(title=document.title)

                # save new listing
                new_listing = Publication_listing(publication=this_doc, author=my_user, page_range=document.pageRange)
                new_listing.save()

        # if article is not in the database
        else:

            # find the publisher
            doc_eid = document.eid
            data_retrieval = AbstractRetrieval(doc_eid, view='FULL')
            publisher = data_retrieval.publisher

            # save new doc
            new_doc = Publication(title=document.title,
                                  document_id=document.doi,
                                  author_names=document.author_names,
                                  author_ids=document.author_ids,
                                  document_type=document.subtypeDescription,
                                  publication_name=document.publicationName,
                                  publisher= publisher,
                                  cover_date=document.coverDate,
                                  cited_by=document.citedby_count)
            new_doc.save()

            # save new listing
            new_listing = Publication_listing(publication=new_doc, author=my_user, page_range=document.pageRange)
            new_listing.save()

    print('Author ' + my_user.username + ' registered')

    return

# finds the documents that havent been downloaded and adds the to db/OK
@login_required
def docs_updator(request):

    keys= ['1']
    create_config(keys)

    my_user= request.user

    myUser_data = AuthorRetrieval(my_user.scopus_id)

    #if my author has less docs in db than in scopus
    if my_user.scopus_document_count < myUser_data.document_count:

        print('Updating document for: ' + my_user.username)

        myAuthor_documents = myUser_data.get_documents()
        #for all the docs in scopus
        for document in myAuthor_documents:
            #if this article exists in the database
            if Publication.objects.filter(title=document.title).exists() == True:
                #if the author is not listed on the article
                if Publication_listing.objects.filter(author=my_user, publication__title=document.title).exists() == False:

                    this_doc=Publication.objects.get(title=document.title)

                    #save new listing
                    new_listing= Publication_listing( publication=this_doc, author=my_user, page_range=document.pageRange)
                    new_listing.save()
            #if article is not in the database
            else:

                # find the publisher
                doc_eid= document.eid
                data_retrieval= AbstractRetrieval(doc_eid, view='FULL')
                publisher= data_retrieval.publisher

                #save new doc
                new_doc= Publication(title=document.title,
                                  document_id=document.doi,
                                  author_names=document.author_names,
                                  author_ids=document.author_ids,
                                  document_type=document.subtypeDescription,
                                  publication_name=document.publicationName,
                                  publisher= publisher,
                                  cover_date=document.coverDate,
                                  cited_by=document.citedby_count)
                new_doc.save()

                #save new listing
                new_listing = Publication_listing(publication=new_doc, author=my_user, page_range=document.pageRange)
                new_listing.save()

    # only count scopus documents because only those changed
    my_user.scopus_document_count= count_scopus_documents(request)
    my_user.save()

    print(my_user.username + ' documents updated!')

    return

# creates the statistics and presents them/OK
@login_required
def publications_creator_presenter(request):

    keys= ['apikey','1']
    create_config(keys)

    # print('your key: ' + config['Authentication']['APIKey'])

    #tsadi is the author now
    my_user = request.user
    my_user.scopus_document_count = count_scopus_documents(request)
    my_user.created_document_count = count_created_documents(request)

    myUser_data = AuthorRetrieval(my_user.scopus_id)

    #if the author has published data that have not been in the database
    if my_user.scopus_document_count != myUser_data.document_count:
        print('Some new Scopus Documents havent been saved to the database!')
        docs_updator(request)

    #get the documents of the author_user
    documents = Publication.objects.filter(user=my_user)

    statistics_dictionary= []
    for document in documents:

        #to load page range
        doc_pagerange= Publication_listing.objects.get(publication= document, author= my_user).page_range
        deleted= Publication_listing.objects.get(publication= document, author= my_user).deleted

        document_statistics= {
            'title': document.title.replace("/", "\\"),
            'document_id': document.document_id,
            'author_names': document.author_names,
            'author_ids': document.author_ids,
            'document_type': document.document_type,
            'publication_name': document.publication_name,
            'publisher': document.publisher,
            'cover_date': document.cover_date,
            'page_range': doc_pagerange,
            'cited_by': document.cited_by,
            'deleted': deleted
        }

        statistics_dictionary.append(document_statistics)

    my_user.scopus_document_count = count_scopus_documents(request)
    my_user.created_document_count = count_created_documents(request)
    total_docs= my_user.scopus_document_count + my_user.created_document_count

    print('Statistics created for: ' + my_user.username)

    user_info= {
        'name': my_user.first_name + ' ' + my_user.last_name,
        'idiotita': my_user.title,
        'scopus_id': my_user.scopus_id
    }

    context= {'user_info': user_info, 'statistics_dictionary': statistics_dictionary, 'total_docs': total_docs}
    return render(request,'accounts/statistics.html', context)

@login_required
def create_publication(request):

    my_user = request.user

    print(my_user.username + 'creates a new Document!')

    form= new_document_form()

    if request.method == 'POST':
        form= new_document_form(request.POST)
        if form.is_valid():
            my_data= form.cleaned_data

            # save new doc
            new_doc = Publication(title=my_data.get('title'),
                                  document_id=my_data.get('document_id'),
                                  author_names=my_data.get('author_names'),
                                  author_ids=my_data.get('author_ids'),
                                  document_type=my_data.get('document_type'),
                                  publication_name=my_data.get('publication_name'),
                                  publisher=my_data.get('publisher'),
                                  cover_date=my_data.get('cover_date'),
                                  cited_by=my_data.get('cited_by'))
            new_doc.save()

            # save new listing
            new_listing = Publication_listing(publication=new_doc, author=my_user)
            new_listing.save()

            my_user.created_document_count = count_created_documents(request)
            my_user.save()

            return redirect('showstatistics')

    context= {'form': form}

    return render(request, 'accounts/create_doc_form.html', context)

# deletes a listing
@login_required
def publication_deleter(request, publication_name):

    my_user = request.user

    print(my_user.username + 'deletes a Document!')

    publication_name.replace("%20", " ")

    print("THIS IS THE PUBLICATION NAME: " + publication_name.replace("+", "/"))

    my_listing= Publication_listing.objects.get(
        publication__title=publication_name.replace("\\", "/"), author=my_user)

    my_listing.deleted= True
    my_listing.save()

    return redirect('showstatistics')

# revives a listing
@login_required
def publication_reviver(request, publication_name):

    my_author = request.user

    print(my_author.username + 'revives a Document!')

    publication_name.replace("%20", " ")

    my_listing= Publication_listing.objects.get(
        publication__title=publication_name.replace("\\", "/"), author=my_author)

    my_listing.deleted= False
    my_listing.save()

    return redirect('showstatistics')

# creates the questioanire from all the previous years/ OK
@login_required
def statistics_all_years_creator(request):

    keys= ['apikey','1']
    create_config(keys)

    my_user = request.user
    my_user.scopus_document_count = count_scopus_documents(request)

    myAuthor_data = AuthorRetrieval(my_user.scopus_id, refresh=True)

    if Report.objects.filter(author=my_user, report_year='Total').exists():
        # checking the date of the last report and the date now
        my_last_report= Report.objects.filter(author= my_user, report_year='Total').last()
        last_report_date= str(my_last_report.created_at)[0:10]

        date_now= datetime.now()
        date_now= str(date_now)[0:10]

        # [0:4] = year, [5:7] = month, [8:10] = day
        last_report_date= int(last_report_date[0:4])*365 + int(last_report_date[5:7])*30 + int(last_report_date[8:10])
        date_now= int(date_now[0:4])*365 + int(date_now[5:7])*30 + int(date_now[8:10])

        # if the author has published data that have not been in the database
        if my_user.scopus_document_count != myAuthor_data.document_count:
            docs_updator(request)

        # if the last report is created less than 10 days before
        if date_now-last_report_date<=10:
            print('Found an report an old report for: ' + my_user.username)
            return my_last_report

    print('Creating an all_year report for: ' + my_user.username)

    #get the documents of the author_user
    documents = Publication.objects.filter(user=my_user)

    articleCounter=0
    conferencePaperCounter=0
    bookChapterCounter=0
    bookCounter=0

    #a list with Publications of uknown type
    list_of_unknown = []
    for document in documents:

        my_listing = Publication_listing.objects.filter(
            publication__title=document.title, author=my_user).last()

        if my_listing.deleted:
            continue

        documentType= lower(document.document_type)

        if documentType == 'article':
            articleCounter+=1
        elif documentType == 'conference paper':
            conferencePaperCounter+=1
        elif documentType == 'book chapter':
            bookChapterCounter+=1
        elif documentType == 'book':
            bookCounter+=1
        else:
            list_of_unknown.append(documentType)

    # finds the "fake" citing numbers and excludes them from the ones in scopus
    fake_citings= find_fake_citedby(request)
    real_citations= allyears_citation_maker(request)
    real_citedby= myAuthor_data.cited_by_count - fake_citings

    newQuestionaire= Report(report_year='Total',
                            article_count= articleCounter,
                            conference_paper_count= conferencePaperCounter,
                            book_chapter_count= bookChapterCounter,
                            book_count= bookCounter,
                            citation_count=real_citations,
                            cited_by_count=real_citedby,
                            author=my_user)

    newQuestionaire.save()

    print('All_year report for: ' + my_user.username + ' created!')

    return newQuestionaire

# presents the data of the questionaire
@login_required
def statistics_all_years_presenter(request):

    my_user= request.user

    newQuestionaire= statistics_all_years_creator(request)

    report_fields={
        'report_year': newQuestionaire.report_year,
        'documents_cited': newQuestionaire.cited_by_count,
        'total_citations': newQuestionaire.citation_count,
        'articles': newQuestionaire.article_count,
        'conference_papers': newQuestionaire.conference_paper_count,
        'book_chapters': newQuestionaire.book_chapter_count,
        'books': newQuestionaire.book_count
    }

    user_info= {
        'name': my_user.first_name + ' ' + my_user.last_name,
        'idiotita': my_user.title,
        'scopus_id': my_user.scopus_id
    }

    context = {'report_fields': report_fields, 'user_info': user_info}
    return render(request, 'accounts/report.html', context)

# changes the report of all the previous years
@login_required
def change_statistics_all_years(request):

    form= change_report_form()

    if request.method == 'POST':
        form= change_report_form(request.POST)
        if form.is_valid():
            my_data= form.cleaned_data
            return redirect('editedtextdownload',
                            citation_count= my_data.get('citation_count'),
                            citedby_count= my_data.get('cited_by_count'))

    context= {'form': form}

    return render(request, 'accounts/change_report_form.html', context)

# downloads the report text of all the previous years
@login_required
def text_download_all_years(request):

    my_user= request.user

    thisQuestionaire = Report.objects.filter(author= my_user, report_year='Total').last()

    # for downloading
    to_download = HttpResponse(content_type='text/plain')
    to_download['Content-Disposition'] = 'attachment; filename="filename.txt"'

    to_download.write(my_user.first_name + ' ' + my_user.last_name + '\n' +
                      'questionaire_year: ' + str(thisQuestionaire.report_year) + '\n' +
                      'documents_cited: ' + str(thisQuestionaire.cited_by_count) + '\n' +
                      'total_citations: ' + str(thisQuestionaire.citation_count) + '\n' +
                      'articles: ' + str(thisQuestionaire.article_count) + '\n' +
                      'conference_papers: ' + str(thisQuestionaire.conference_paper_count)+ '\n' +
                      'book_chapters: ' + str(thisQuestionaire.book_chapter_count)+ '\n' +
                      'books: ' + str(thisQuestionaire.book_count))

    return to_download

@login_required
def edited_text_download_all_years(request, citation_count, citedby_count):

    my_user= request.user

    thisQuestionaire = Report.objects.filter(author= my_user).last()

    # for downloading
    to_download = HttpResponse(content_type='text/plain')
    to_download['Content-Disposition'] = 'attachment; filename="filename.txt"'

    to_download.write(my_user.first_name + ' ' + my_user.last_name + '\n' +
                      'questionaire_year: ' + str(thisQuestionaire.report_year) + '\n' +
                      'documents_cited: ' + citedby_count + '\n' +
                      'total_citations: ' + citation_count + '\n' +
                      'articles: ' + str(thisQuestionaire.article_count)+ '\n' +
                      'conference_papers: ' + str(thisQuestionaire.conference_paper_count)+ '\n' +
                      'book_chapters: ' + str(thisQuestionaire.book_chapter_count)+ '\n' +
                      'books: ' + str(thisQuestionaire.book_count))

    return to_download

# creates the report of the last year
@login_required
def report_last_year_creator(request):

    keys= ['apikey','1']
    create_config(keys)

    my_user= request.user
    my_user.scopus_document_count = count_scopus_documents(request)

    myAuthor_data = AuthorRetrieval(my_user.scopus_id)

    date_now= datetime.now()
    date_now= str(date_now)[0:10]

    # requested_year= date_now[0:4]
    requested_year= date_now[0:4]

    # checking the date of the last report and the date now(prosorina 2021)
    if Report.objects.filter(author= my_user, report_year=requested_year).exists():
        # na to allaksw se-> date.now[0:4]
        my_last_report= Report.objects.filter(author= my_user, report_year=requested_year).last()
        last_report_date= str(my_last_report.created_at)[0:10]

        # [0:4] = year, [5:7] = month, [8:10] = day
        last_report_date= int(last_report_date[0:4])*365 + int(last_report_date[5:7])*30 + int(last_report_date[8:10])
        date_now= int(date_now[0:4])*365 + int(date_now[5:7])*30 + int(date_now[8:10])

        # if the author has published data that have not been in the database
        if my_user.scopus_document_count != myAuthor_data.document_count:
            docs_updator(request)

        # if the last report is created less than 10 days before
        if date_now-last_report_date<=10:
            return my_last_report

    # get the documents of the author_user
    documents = Publication.objects.filter(user=my_user)

    articleCounter = 0
    conferencePaperCounter = 0
    bookChapterCounter = 0
    bookCounter = 0

    # a list with Publications of uknown type
    list_of_unknown = []
    counter = 0
    for document in documents:

        documentType = lower(document.document_type)
        date = document.cover_date
        year = date[0:4]

        if year == requested_year:
            if documentType == 'article':
                articleCounter += 1
            elif documentType == 'conference paper':
                conferencePaperCounter += 1
            elif documentType == 'book chapter':
                bookChapterCounter += 1
            elif documentType == 'book':
                bookCounter += 1
            else:
                list_of_unknown.append(documentType)

    # finds the "fake" citing numbers and excludes them from the ones in scopus
    real_citations= lastyear_citation_maker(request)
    real_citedby= '-1'

    newQuestionaire= Report(report_year= requested_year,
                                  article_count= articleCounter,
                                  conference_paper_count= conferencePaperCounter,
                                  book_chapter_count= bookChapterCounter,
                                  book_count= bookCounter,
                                  citation_count=real_citations,
                                  cited_by_count=real_citedby,
                                  author=my_user)

    newQuestionaire.save()

    return newQuestionaire

# presents the data of the questionaire
@login_required
def report_last_year_presenter(request):

    my_user = request.user

    date_now= datetime.now()
    date_now= str(date_now)[0:4]

    newQuestionaire= report_last_year_creator(request)

    questionaire_fields={
        'questionaire_year': newQuestionaire.report_year,
        'documents_cited': newQuestionaire.cited_by_count,
        'total_citations': newQuestionaire.citation_count,
        'articles': newQuestionaire.article_count,
        'conference_papers': newQuestionaire.conference_paper_count,
        'book_chapters': newQuestionaire.book_chapter_count,
        'books': newQuestionaire.book_count
    }

    user_info= {
        'name': my_user.first_name + ' ' + my_user.last_name,
        'idiotita': my_user.title,
        'scopus_id': my_user.scopus_id
    }

    context = {'user_info': user_info, 'questionaire_fields': questionaire_fields}
    return render(request, 'accounts/lastyear_report.html', context)

# changes the report of the previous year
@login_required
def change_report_last_year(request):

        newQuestionaire = report_last_year_creator(request)

        questionaire_fields = {
            'questionaire_year': newQuestionaire.questionaire_year,
            'documents_cited': newQuestionaire.cited_by_count,
            'total_citations': newQuestionaire.citation_count,
            'articles': newQuestionaire.article_count,
            'conference_papers': newQuestionaire.conference_paper_count,
            'book_chapters': newQuestionaire.book_chapter_count,
            'books': newQuestionaire.book_count
        }

        context = {'questionaire_fields': questionaire_fields}

        return render(request, 'accounts/change_report_form.html', context)

# downloads the report text of the previous year
@login_required
def text_download_last_year(request):

    my_user= request.user

    date_now= datetime.now()
    date_now= str(date_now)[0:10]

    # requested_year= date_now[0:4]
    requested_year= date_now[0:4]

    thisQuestionaire = Report.objects.filter(author= my_user, report_year=requested_year).last()

    # for downloading
    to_download = HttpResponse(content_type='text/plain')
    to_download['Content-Disposition'] = 'attachment; filename="filename.txt"'

    to_download.write(my_user.first_name + ' ' + my_user.last_name + '\n' +
                      'questionaire_year: ' + str(thisQuestionaire.report_year) + '\n' +
                      'documents_cited: ' + str(thisQuestionaire.cited_by_count) + '\n' +
                      'total_citations: ' + str(thisQuestionaire.citation_count) + '\n' +
                      'articles: ' + str(thisQuestionaire.article_count) + '\n' +
                      'conference_papers: ' + str(thisQuestionaire.conference_paper_count)+ '\n' +
                      'book_chapters: ' + str(thisQuestionaire.book_chapter_count)+ '\n' +
                      'books: ' + str(thisQuestionaire.book_count))

    return to_download
    

@login_required
def count_scopus_documents(request):

    my_user= request.user

    real_docs = Publication.objects.filter(user=my_user)
    counter= 0
    for document in real_docs:

        my_listing= Publication_listing.objects.get(
            publication=document, author=my_user)

        if document.scopus_document and my_listing.deleted==False:
            counter= counter+1

    return counter

@login_required
def count_created_documents(request):

    my_user = request.user

    real_docs = Publication.objects.filter(user=my_user)
    counter= 0
    for document in real_docs:

        my_listing= Publication_listing.objects.get(
            publication=document, author=my_user)

        if document.scopus_document==False and my_listing.deleted==False:
            counter= counter+1

    return counter

@login_required
def find_fake_citedby(request):

    keys= ['1']
    create_config(keys)

    my_user = request.user

    myAuthor_data = AuthorRetrieval(my_user.scopus_id)

    author_documents= myAuthor_data.get_documents()

    fake_citedby_counter=0
    for this_document in author_documents:

        # get the id of the first document
        doc_eid= this_document.eid

        # get the data about the document
        data_retrieval = AbstractRetrieval(doc_eid, view='FULL')

        # get the references of the document
        document_references= data_retrieval.references

        if document_references is None:
            continue

        for this_reference in document_references:

            # get the authors of the first doc
            authors= this_reference.authors

            if authors.lower().count(lower(my_user.last_name)) > 0:
                fake_citedby_counter= fake_citedby_counter + 1
                break

    print('fake cited_by: ' + str(fake_citedby_counter))
    return fake_citedby_counter

@login_required
def delete_doubles(request):



    return HttpResponse('in proccess')

@login_required
def find_lastyear_citations(request):

    keys= ['1']
    create_config(keys)

    my_user= request.user

    myAuthor_data = AuthorRetrieval(my_user.scopus_id)
    author_documents= myAuthor_data.get_documents()

    date_now= datetime.now()
    date_now= str(date_now)[0:4]

    citation_counter=0
    for this_document in author_documents:
        # get the id of the first document
        doc_eid = this_document.eid
        data_retrieval = AbstractRetrieval(doc_eid, view='FULL', refresh=True)

        # anti gia 2021 na balw date_now
        if data_retrieval.coverDate[0:4]==date_now:
            citation_counter= citation_counter + data_retrieval.citedby_count

    fake_citation_counter = 0
    for this_document in author_documents:

        # get the id of the first document
        doc_eid = this_document.eid

        # get the data about the document
        data_retrieval = AbstractRetrieval(doc_eid, view='FULL')

        # anti gia 2021 na balw date_now
        if data_retrieval.coverDate[0:4] == date_now:

            # get the references of the document
            document_references = data_retrieval.references

            for this_reference in document_references:


                # get the authors of the first doc
                authors = this_reference.authors
                publication_year= this_reference.publicationyear

                if authors.lower().count(lower(my_user.last_name)) > 0 and publication_year == date_now:
                    fake_citation_counter = fake_citation_counter + 1


    real_citations= citation_counter - fake_citation_counter

    return real_citations

def lastyear_citation_maker(request):
    keys= ['1']
    create_config(keys)

    my_user = request.user

    # retrieves author data
    myUser_data = AuthorRetrieval(my_user.scopus_id)

    #get the documents of the author_user
    documents = myUser_data.get_documents()

    date_now= datetime.now()
    date_now= str(date_now)[0:10]

    # requested_year= date_now[0:4]
    requested_year= date_now[0:4]

    citation_counter= 0
    for this_document in documents:

        if requested_year == this_document.coverDate[0:4]:

            # get the id of the first document
            doc_eid= this_document.eid

            identifier = [doc_eid[7:18]]
            co = CitationOverview(identifier, start=this_document.coverDate[0:4],citation='exclude-self', refresh=True)

            if co.grandTotal > 0:
                citation_counter = citation_counter + co.grandTotal


    print(str(citation_counter))

    return citation_counter

def allyears_citation_maker(request):

    keys= ['1']
    create_config(keys)

    my_user = request.user

    # retrieves author data
    myUser_data = AuthorRetrieval(my_user.scopus_id)

    #get the documents of the author_user
    documents = myUser_data.get_documents()

    citation_counter= 0
    for this_document in documents:

        # get the id of the first document
        doc_eid= this_document.eid

        identifier = [doc_eid[7:18]]
        co = CitationOverview(identifier, start=this_document.coverDate[0:4],citation='exclude-self', refresh=True)

        if co.grandTotal > 0:
            citation_counter = citation_counter + co.grandTotal


    print(str(citation_counter))

    return citation_counter

def admin_fullreport_creator(query):

    keys= ['1']
    create_config(keys)

    if User.objects.filter(last_name=query).exists() == False:
        return -1
    else:
        my_user = User.objects.get(last_name=query)

    if Report.objects.filter(author=my_user, report_year='Total').exists():
        my_last_report= Report.objects.filter(author= my_user, report_year='Total').last()
        return my_last_report
    else:
        return -1

def admin_lastyearreport_creator(query):

    keys= ['1']
    create_config(keys)

    if User.objects.filter(last_name=query).exists() == False:
        return -1
    else:
        my_user = User.objects.get(last_name=query)

    date_now= datetime.now()
    date_now= str(date_now)[0:10]

    # requested_year= date_now[0:4]
    requested_year= date_now[0:4]

    if Report.objects.filter(author=my_user, report_year=requested_year).exists():
        my_last_report= Report.objects.filter(author= my_user, report_year=requested_year).last()
        return my_last_report
    else:
        return -1

def admin_fiveyearreport_creator(query):

    keys= ['1']
    create_config(keys)

    if User.objects.filter(last_name=query).exists() == False:
        return -1
    else:
        my_user = User.objects.get(last_name=query)

    if Report.objects.filter(author=my_user, report_year='5years').exists():
        my_last_report= Report.objects.filter(author= my_user, report_year='5years').last()
        return my_last_report
    else:
        return -1

def admin_querysearch(request):

    query = request.GET.get('secret_key', False)

    if query != False:
        alltime_report= admin_fullreport_creator(query.upper())

        if alltime_report != -1:

            alltime_report_fields= {
                'alltime_report_year': alltime_report.report_year,
                'alltime_documents_cited': alltime_report.cited_by_count,
                'alltime_total_citations': alltime_report.citation_count,
                'alltime_articles': alltime_report.article_count,
                'alltime_conference_papers': alltime_report.conference_paper_count,
                'alltime_book_chapters': alltime_report.book_chapter_count,
                'alltime_books': alltime_report.book_count
            }

            my_user= User.objects.get(last_name=query.upper())

            user_info={
                'name': my_user.first_name + ' ' + my_user.last_name,
                'email': my_user.username,
                'idiotita': my_user.title,
                'scopus_id': my_user.scopus_id
            }

            lastyear_report= admin_lastyearreport_creator(query.upper())

            if lastyear_report != -1:
                alltime_report_fields = {
                    'alltime_report_year': alltime_report.report_year,
                    'alltime_documents_cited': alltime_report.cited_by_count,
                    'alltime_total_citations': alltime_report.citation_count,
                    'alltime_articles': alltime_report.article_count,
                    'alltime_conference_papers': alltime_report.conference_paper_count,
                    'alltime_book_chapters': alltime_report.book_chapter_count,
                    'alltime_books': alltime_report.book_count,
                    'lastyear_report_year': lastyear_report.report_year,
                    'lastyear_documents_cited': lastyear_report.cited_by_count,
                    'lastyear_total_citations': lastyear_report.citation_count,
                    'lastyear_articles': lastyear_report.article_count,
                    'lastyear_conference_papers': lastyear_report.conference_paper_count,
                    'lastyear_book_chapters': lastyear_report.book_chapter_count,
                    'lastyear_books': lastyear_report.book_count
                }

                fiveyears_report = admin_fiveyearreport_creator(query.upper())

                if lastyear_report != -1:
                    alltime_report_fields = {
                        'alltime_report_year': alltime_report.report_year,
                        'alltime_documents_cited': alltime_report.cited_by_count,
                        'alltime_total_citations': alltime_report.citation_count,
                        'alltime_articles': alltime_report.article_count,
                        'alltime_conference_papers': alltime_report.conference_paper_count,
                        'alltime_book_chapters': alltime_report.book_chapter_count,
                        'alltime_books': alltime_report.book_count,
                        'lastyear_report_year': lastyear_report.report_year,
                        'lastyear_documents_cited': lastyear_report.cited_by_count,
                        'lastyear_total_citations': lastyear_report.citation_count,
                        'lastyear_articles': lastyear_report.article_count,
                        'lastyear_conference_papers': lastyear_report.conference_paper_count,
                        'lastyear_book_chapters': lastyear_report.book_chapter_count,
                        'lastyear_books': lastyear_report.book_count,
                        'fiveyears_report_year': fiveyears_report.report_year,
                        'fiveyears_documents_cited': fiveyears_report.cited_by_count,
                        'fiveyears_total_citations': fiveyears_report.citation_count,
                        'fiveyears_articles': fiveyears_report.article_count,
                        'fiveyears_conference_papers': fiveyears_report.conference_paper_count,
                        'fiveyears_book_chapters': fiveyears_report.book_chapter_count,
                        'fiveyears_books': fiveyears_report.book_count
                    }

            context = {'report_fields': alltime_report_fields, 'user_info': user_info}
            return render(request, 'accounts/admin_results.html', context)

        else:
            return HttpResponse('unkown error')

    return render(request, 'accounts/admin_query.html')

def fiveyears_citation_maker(request):
    keys= ['1']
    create_config(keys)

    my_user = request.user

    # retrieves author data
    myUser_data = AuthorRetrieval(my_user.scopus_id)

    #get the documents of the author_user
    documents = myUser_data.get_documents()

    date_now= datetime.now()
    date_now= str(date_now)[0:10]

    # requested_year= date_now[0:4]
    requested_year= int(date_now[0:4]) - 5

    citation_counter= 0
    for this_document in documents:

        if str(requested_year) <= this_document.coverDate[0:4]:

            # get the id of the first document
            doc_eid= this_document.eid

            identifier = [doc_eid[7:18]]
            co = CitationOverview(identifier, start=this_document.coverDate[0:4],citation='exclude-self', refresh=True)

            if co.grandTotal > 0:
                citation_counter = citation_counter + co.grandTotal

    return citation_counter

@login_required
def fiveyears_report_creator(request):

    keys= ['1']
    create_config(keys)

    my_user= request.user
    my_user.scopus_document_count = count_scopus_documents(request)

    myAuthor_data = AuthorRetrieval(my_user.scopus_id)

    date_now= datetime.now()
    date_now= str(date_now)[0:10]

    # requested_year= date_now[0:4]
    year_now= int(date_now[0:4])
    wanted_date = year_now - 5

    # checking the date of the last report and the date now(prosorina 2021)
    if Report.objects.filter(author= my_user, report_year='5years').exists():
        # na to allaksw se-> date.now[0:4]
        my_last_report= Report.objects.filter(author= my_user, report_year='5years').last()
        last_report_date= str(my_last_report.created_at)[0:10]

        # [0:4] = year, [5:7] = month, [8:10] = day
        last_report_date= int(last_report_date[0:4])*365 + int(last_report_date[5:7])*30 + int(last_report_date[8:10])
        date_now= int(date_now[0:4])*365 + int(date_now[5:7])*30 + int(date_now[8:10])

        # if the author has published data that have not been in the database
        if my_user.scopus_document_count != myAuthor_data.document_count:
            docs_updator(request)

        # if the last report is created less than 10 days before
        if int(date_now-last_report_date)<=10:
            return my_last_report

    # get the documents of the author_user
    documents = Publication.objects.filter(user=my_user)

    articleCounter = 0
    conferencePaperCounter = 0
    bookChapterCounter = 0
    bookCounter = 0

    # a list with Publications of uknown type
    list_of_unknown = []
    counter = 0
    for document in documents:

        documentType = lower(document.document_type)
        date = document.cover_date
        year = date[0:4]

        if year >= str(wanted_date):
            if documentType == 'article':
                articleCounter += 1
            elif documentType == 'conference paper':
                conferencePaperCounter += 1
            elif documentType == 'book chapter':
                bookChapterCounter += 1
            elif documentType == 'book':
                bookCounter += 1
            else:
                list_of_unknown.append(documentType)

    # finds the "fake" citing numbers and excludes them from the ones in scopus
    real_citations= fiveyears_citation_maker(request)
    real_citedby= '-1'

    newQuestionaire= Report(report_year= '5years',
                                  article_count= articleCounter,
                                  conference_paper_count= conferencePaperCounter,
                                  book_chapter_count= bookChapterCounter,
                                  book_count= bookCounter,
                                  citation_count=real_citations,
                                  cited_by_count=real_citedby,
                                  author=my_user)

    newQuestionaire.save()

    return newQuestionaire

def fiveyear_report_presenter(request):

    my_user = request.user

    newQuestionaire= fiveyears_report_creator(request)

    questionaire_fields={
        'questionaire_year': newQuestionaire.report_year,
        'documents_cited': newQuestionaire.cited_by_count,
        'total_citations': newQuestionaire.citation_count,
        'articles': newQuestionaire.article_count,
        'conference_papers': newQuestionaire.conference_paper_count,
        'book_chapters': newQuestionaire.book_chapter_count,
        'books': newQuestionaire.book_count
    }

    user_info= {
        'name': my_user.first_name + ' ' + my_user.last_name,
        'idiotita': my_user.title,
        'scopus_id': my_user.scopus_id
    }

    context = {'user_info': user_info, 'questionaire_fields': questionaire_fields}
    return render(request, 'accounts/fiveyears_report.html', context)

# downloads the report text of the previous five years
@login_required
def text_download_five_years(request):

    my_user= request.user

    thisQuestionaire = Report.objects.filter(author= my_user, report_year='5years').last()

    # for downloading
    to_download = HttpResponse(content_type='text/plain')
    to_download['Content-Disposition'] = 'attachment; filename="filename.txt"'

    to_download.write(my_user.first_name + ' ' + my_user.last_name + '\n' +
                      'questionaire_year: ' + str(thisQuestionaire.report_year) + '\n' +
                      'documents_cited: ' + str(thisQuestionaire.cited_by_count) + '\n' +
                      'total_citations: ' + str(thisQuestionaire.citation_count) + '\n' +
                      'articles: ' + str(thisQuestionaire.article_count) + '\n' +
                      'conference_papers: ' + str(thisQuestionaire.conference_paper_count)+ '\n' +
                      'book_chapters: ' + str(thisQuestionaire.book_chapter_count)+ '\n' +
                      'books: ' + str(thisQuestionaire.book_count))

    return to_download

'accounts/fiveyears_report.html'
def admin_see_hua(request):

    keys= ['apikey','1']
    create_config(keys)

    hua= AffiliationRetrieval('60012296', refresh=True)

    print(hua.author_count)
    print(hua.document_count)
    print(hua.state)
    print(hua.postal_code)
    print(hua)

    context={'author_count': hua.author_count, 'document_count': hua.document_count}

    return render(request, 'accounts/admintotalstats.html', context)
