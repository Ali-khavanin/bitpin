from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Post, Rating

from django.db.models import Count, Avg, Case, When, IntegerField
from rest_framework import status
from django.shortcuts import get_object_or_404


class PostList(APIView):
    def get(self, request):
        user = request.user

        posts = Post.objects.annotate(
            count_ratings=Count('ratings'),
            avg_score=Avg('ratings__score'),
            user_rating=Case(
                When(ratings__user=user, then='ratings__score'),
                default=None,
                output_field=IntegerField()
            ),
        ).all()

        post_data = []
        for post in posts:
            user_score = post.user_rating if user.is_authenticated else None
            avg_score = post.avg_score if post.count_ratings != 0 else None
            post_data.append(
                {
                    'title': post.title,
                    'count_users_scored': post.count_ratings,
                    'average_score': avg_score,
                    'user_score': user_score
                }
            )

        return Response(post_data, status=status.HTTP_200_OK)


class RatePost(APIView):
    def post(self, request, post_id):
        user = request.user
        score = request.data.get('score')
        try:
            if not (0 <= score <= 5):
                return Response(
                    {
                        'error': "score must be between 0 to 5"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        except TypeError as exp:
            return Response(
                {'error': exp}, status=status.HTTP_400_BAD_REQUEST
            )
        post = get_object_or_404(Post, pk=post_id)
        score, created = Rating.objects.get_or_create(post=post, user=user, defaults={'score': score})

        if not created:
            score.score = score # sorry about the bad naming :/ it means that go to the score variable
            # score variable is a Rating type object, and it has a score attribute and set it to the given score
            # from the user
            score.save()

        return Response(status=status.HTTP_200_OK)
