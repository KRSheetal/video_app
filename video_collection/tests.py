from django.test import TestCase
from django.urls import reverse
from .models import Video
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError

# Create your tests here.

class TestHomePageMessage(TestCase):

    def test_app_title_message_shown_on_home_page(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertContains(response, 'Exercise Videos')

class TestAddVideos(TestCase):
    def test_add_video(self):

        valid_video = {
            'name': 'yoga',
            'url' : 'https://www.youtube.com/watch?v=XeXz8fIZDCE',
            'notes': 'Yoga for lower back'
        }

        url = reverse('add_video')
        response = self.client.post(url, data=valid_video, follow=True)

        self.assertTemplateUsed('video_collection/video_list.html')

        # does the video list show the new video?
        self.assertContains(response, 'yoga')
        self.assertContains(response, 'Yoga for lower back')
        self.assertContains(response, 'https://www.youtube.com/watch?v=XeXz8fIZDCE')

        video_count = Video.objects.count()
        self.assertEqual(1, video_count)

        video = Video.objects.first()

        self.assertEqual('yoga', video.name)
        self.assertEqual('https://www.youtube.com/watch?v=XeXz8fIZDCE', video.url)
        self.assertEqual('Yoga for lower back', video.notes)
        self.assertEqual('XeXz8fIZDCE', video.video_id)


    def test_add_duplicate_video_not_added(self):

        # Since an integrity error is raised, the database has to be rolled back to the state before this 
        # action (here, adding a duplicate video) was attempted. This is a separate transaction so the 
        # database might be in a weird state and future queries in this method can fail with atomic transaction errors. 
        # the solution is to ensure the entire transation is in an atomic block so the attempted save and subsequent 
        # rollback are completely finished before more DB transactions - like the count query - are attempted.

        # Most of this is handled automatically in a view function, but we have to deal with it here. 

        with transaction.atomic():
            new_video = {
                'name': 'yoga',
                'url': 'https://www.youtube.com/watch?v=4vTJHUDB5ak',
                'notes': 'yoga for neck and shoulders'
            }

            # Create a video with this data in the database
            # the ** syntax unpacks the dictonary and converts it into function arguments
            # https://python-reference.readthedocs.io/en/latest/docs/operators/dict_unpack.html
            # Video.objects.create(**new_video)
            # with the new_video dictionary above is equivalent to 
            # Video.objects.create(name='yoga', url='https://www.youtube.com/watch?v=4vTJHUDB5ak', notes='for neck and shoulders')
            Video.objects.create(**new_video)

            video_count = Video.objects.count()
            self.assertEqual(1, video_count)

        with transaction.atomic():
            # try to create it again    
            response = self.client.post(reverse('add_video'), data=new_video)

            # same template, the add form 
            self.assertTemplateUsed('video_collection/add.html')

            messages = response.context['messages']
            message_texts = [ message.message for message in messages ]
            self.assertIn('You already added that video', message_texts)

            self.assertContains(response, 'You already added that video')  # and message displayed on page 

        # still one video in the database 
        video_count = Video.objects.count()
        self.assertEqual(1, video_count)


    def test_add_video_invalid_url_not_added(self):
        invalid_video_urls = [
            'https://www.youtube.com/watch',
            'https://www.youtube.com/watch?',
            'https://www.youtube.com/watch?abc=342',
            'https://www.youtube.com/watch?v=',
            'https://www.youtubekids.com/watch?',
            'https://github.com',
            'https://minneapolis.edu',
            'https://minneapolis.edu?v=423423'
        ]

        for invalid_video_url in invalid_video_urls:

            new_video = {
                'name': 'example',
                'url' : invalid_video_url,
                'notes': 'example notes'
            }

            url = reverse('add_video')
            response = self.client.post(url, new_video)

            self.assertTemplateNotUsed('video_collection/add.html')
            messages = response.context['messages']
            message_texts = [message.message for message in messages]

            self.assertIn('Invalid YouTube URL', message_texts)
            self.assertIn('Please check the data entered', message_texts)

            video_count = Video.objects.count()
            self.assertEqual(0, video_count)


class TestVideoList(TestCase):
    
    def test_all_videos_displayed_in_correct_order(self):

        v1 = Video.objects.create(name='ZXY', notes='example1', url='https://www.youtube.com/watch?v=123')
        v2 = Video.objects.create(name='abc', notes='example2', url='https://www.youtube.com/watch?v=234')
        v3 = Video.objects.create(name='AAA', notes='example3', url='https://www.youtube.com/watch?v=4567')
        v4 = Video.objects.create(name='lmn', notes='example4', url='https://www.youtube.com/watch?v=67345')

        expected_video_order = [ v3, v2, v4, v1 ]  # expected order of the video list

        url = reverse('video_list')
        response = self.client.get(url)

        videos_in_template = list(response.context['videos']) # convert to python list

        self.assertEqual(videos_in_template, expected_video_order)

    def test_no_video_message(self):
        url = reverse('video_list')
        response = self.client.get(url)
        self.assertContains(response, 'No videos.') 
        self.assertEqual(0, len(response.context['videos']))

    def test_video_number_message_one_video(self):
        v1 = Video.objects.create(name='ZXY', notes='example1', url='https://www.youtube.com/watch?v=123')
        url = reverse('video_list')
        response = self.client.get(url)

        self.assertContains(response, '1 video')
        self.assertNotContains(response, '1 videos')

    def test_video_number_message_two_videos(self):
        v1 = Video.objects.create(name='ZXY', notes='example1', url='https://www.youtube.com/watch?v=123')
        v2 = Video.objects.create(name='abc', notes='example2', url='https://www.youtube.com/watch?v=234')
        url = reverse('video_list')
        response = self.client.get(url)

        self.assertContains(response, '2 videos')


class TestVideoSearch(TestCase):
    
    # search only videos matching search term
    def test_video_search_matches(self):
        v1 = Video.objects.create(name='ABC', notes='example', url='https://www.youtube.com/watch?v=456')
        v2 = Video.objects.create(name='nope', notes='example', url='https://www.youtube.com/watch?v=789')
        v3 = Video.objects.create(name='abc', notes='example', url='https://www.youtube.com/watch?v=123')
        v4 = Video.objects.create(name='hello aBc!!!', notes='example', url='https://www.youtube.com/watch?v=101')
        
        expected_video_order = [v1, v3, v4] 
        response = self.client.get(reverse('video_list') + '?search_term=abc')
        videos_in_template = list(response.context['videos'])
        self.assertEqual(expected_video_order, videos_in_template)


    def test_video_search_no_matches(self):
        v1 = Video.objects.create(name='ABC', notes='example', url='https://www.youtube.com/watch?v=456')
        v2 = Video.objects.create(name='nope', notes='example', url='https://www.youtube.com/watch?v=789')
        v3 = Video.objects.create(name='abc', notes='example', url='https://www.youtube.com/watch?v=123')
        v4 = Video.objects.create(name='hello aBc!!!', notes='example', url='https://www.youtube.com/watch?v=101')
        
        expected_video_order = []  # empty list 
        response = self.client.get(reverse('video_list') + '?search_term=kittens') # no video must be returned
        videos_in_template = list(response.context['videos']) # convert to python list
        self.assertEqual(expected_video_order, videos_in_template)
        self.assertContains(response, 'No videos')

class TestVideoModel(TestCase):

    def test_create_id(self):
        video = Video.objects.create(name='example', url='https://www.youtube.com/watch?v=XeXz8fIZDCE')
        self.assertEqual('XeXz8fIZDCE', video.video_id)
    
    def test_create_id_valid_url_with_time_parameter(self):
        # a video that is playing and paused may have a timestamp in the query
        video = Video.objects.create(name='example', url='https://www.youtube.com/watch?v=XeXz8fIZDCE&ts=14')
        self.assertEqual('XeXz8fIZDCE', video.video_id)

    def test_create_video_notes_optional(self):
        v1 = Video.objects.create(name='example', url='https://www.youtube.com/watch?v=67890')
        v2 = Video.objects.create(name='different example', notes='example', url='https://www.youtube.com/watch?v=12345')
        expected_videos = [v1, v2]

        database_videos = Video.objects.all()
        self.assertCountEqual(expected_videos, database_videos) # check contents of two lists/iterables but order does not matter

    def test_invalid_url_raises_validation_error(self):
        invalid_video_urls = [
            'https://www.youtube.com/watch',
            'https://www.youtube.com/watch/somethingelse/',
            'https://www.youtube.com/watch/somethingelse?v=1234567',
            'https://www.youtube.com/watch?',
            'https://www.youtube.com/watch?abc=342',
            'https://www.youtube.com/watch?v=',
            'https://www.youtubekids.com/watch?',
            '12312423',
            'hhhhhhhhttps://www.youtube.com/watch',
            'http://www.youtube.com/watch',
            'https://github.com',
            'https://minneapolis.edu',
            'https://minneapolis.edu?v=423423'
        ]

        for invalid_video_url in invalid_video_urls:
            with self.assertRaises(ValidationError):
                Video.objects.create(name='example', url=invalid_video_url, notes='example noteS')

        self.assertEqual(0, Video.objects.count())

    def test_duplicate_video_raises_integrity_error(self):
        Video.objects.create(name='ZXY', url='https://www.youtube.com/watch?v=IODxDxX7oi4')
        with self.assertRaises(IntegrityError):
            Video.objects.create(name='ZXY', url='https://www.youtube.com/watch?v=IODxDxX7oi4')
