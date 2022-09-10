from django.urls import path, include

from . import views

urlpatterns = [
    # Index view
    path('', views.index, name = 'index'),
    path('accounts/profile/', views.profile, name = 'profile'),
    path('accounts/forgotpassword/', views.forgotpassword, name = 'forgotpassword'),
    path('accounts/logout/', views.logoutView, name = 'logout'),
    path('accounts/', include('django.contrib.auth.urls')),

    path('first-login/', views.firsttime_login, name='firstlogin'),
    path('set-id/', views.set_user, name='setuser'),

    path('main-page', views.main_page, name='mainpage'),

    path('show-statistics', views.publications_creator_presenter, name='showstatistics'),
    path('create-document', views.create_publication, name='createdocument'),
    path('delete-stats/<str:publication_name>', views.publication_deleter, name='deletestats'),
    path('revive-stats/<str:publication_name>', views.publication_reviver, name='revivestats'),

    path('full-report', views.statistics_all_years_presenter, name='fullreport'),
    path('change-report', views.change_statistics_all_years, name='changereport'),
    path('text-download', views.text_download_all_years, name='textdownload'),
    path('text-download-one', views.text_download_last_year, name='textdownloadone'),
    path('text-download-five', views.text_download_five_years, name='textdownloadfive'),
    path('edited-text-download/<str:citation_count>/<str:citedby_count>', views.edited_text_download_all_years,
         name='editedtextdownload'),

    path('last-year-report', views.report_last_year_presenter, name='lastyearreport'),
    path('five-year-report', views.fiveyear_report_presenter, name='fiveyearreport'),

    path('citation-test/', views.allyears_citation_maker, name='citationtest'),
    path('admin-test/', views.admin_querysearch, name='admintest'),
    path('see-hua/', views.admin_see_hua, name='adminseehua'),

]
