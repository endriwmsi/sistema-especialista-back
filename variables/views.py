from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Questions, Rules
from .serializer import QuestionsSerializer, RulesSerializer


class QuestionsList(APIView):
    def get(self, request):
        questions = Questions.objects.all()
        serializer = QuestionsSerializer(questions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = QuestionsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RulesList(APIView):
    def get(self, request):
        rules = Rules.objects.all()
        serializer = RulesSerializer(rules, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Extrai os dados da requisição
        data = request.data
        name = data.get('name', '')
        result = data.get('result', '')
        questions_data = data.get('questions', [])

        # Cria a regra sem associar perguntas
        rule_serializer = RulesSerializer(
            data={'name': name, 'result': result})
        if rule_serializer.is_valid():
            rule = rule_serializer.save()

            # Associa as perguntas à regra e salva novas perguntas se não existirem
            for question_data in questions_data:
                if isinstance(question_data, int):  # Se é um ID
                    question = get_object_or_404(Questions, pk=question_data)
                elif isinstance(question_data, dict):  # Se é um objeto de pergunta
                    title = question_data.get('title', '')
                    answer = question_data.get('answer', None)

                    # Tenta obter a pergunta do banco de dados
                    question = Questions.objects.filter(
                        title=title, answer=answer).first()

                    # Se a pergunta não existe, cria uma nova
                    if not question:
                        question_serializer = QuestionsSerializer(
                            data={'title': title, 'answer': answer})
                        if question_serializer.is_valid():
                            question = question_serializer.save()
                        else:
                            # Se a criação da pergunta falhar, você pode querer lidar com isso de acordo
                            return Response(question_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Se o formato da pergunta não é reconhecido, retorne um erro
                    return Response({'error': 'Formato de pergunta não reconhecido'}, status=status.HTTP_400_BAD_REQUEST)

                # Associa a pergunta à regra
                rule.questions.add(question)

            # Atualiza o serializer da regra para incluir as perguntas
            updated_rule_serializer = RulesSerializer(rule)
            return Response(updated_rule_serializer.data, status=status.HTTP_201_CREATED)

        return Response(rule_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuestionDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Questions.objects.all()
    serializer_class = QuestionsSerializer

    def patch(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class RuleDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Rules.objects.all()
    serializer_class = RulesSerializer

    def patch(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
