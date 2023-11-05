from django.test import TestCase
from django.urls import reverse
from .models import Video

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
            ######



class TestVideoList(TestCase):
    pass

class TestVideoSearch(TestCase):
    pass

class TestVideoModel(TestCase):
    pass
