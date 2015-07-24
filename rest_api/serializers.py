from rest_framework import serializers
from cwe.models import CWE
from muo.models import MisuseCase
from muo.models import UseCase


class CWESerializer(serializers.ModelSerializer):
    class Meta:
        # Associate this serializer with CWE
        model = CWE
        # The fields that this serializer processes
        fields = ('id',    # The ID of the CWE
                  'code',  # The code of the CWE
                  'name',  # The name of the CWE
                  )


class MisuseCaseSerializer(serializers.ModelSerializer):
    class Meta:
        # Associate this serializer with MisuseCase
        model = MisuseCase
        # The fields that this serializer processes
        fields = ('id',     # The ID of the misuse case
                  'name',   # The name of the misuse case
                  'misuse_case_description',
                  'misuse_case_primary_actor',
                  'misuse_case_secondary_actor',
                  'misuse_case_precondition',
                  'misuse_case_flow_of_events',
                  'misuse_case_postcondition',
                  'misuse_case_assumption',
                  'misuse_case_source',
                  )


class UseCaseSerializer(serializers.ModelSerializer):
    class Meta:
        # Associate this serializer with UseCase
        model = UseCase
        # The fields that this serializer processes
        fields = ('id',     # The ID of the use case
                  'name',   # The name of the use case
                  'use_case_description',
                  'use_case_primary_actor',
                  'use_case_secondary_actor',
                  'use_case_precondition',
                  'use_case_flow_of_events',
                  'use_case_postcondition',
                  'use_case_assumption',
                  'use_case_source',
                  'osr_pattern_type',
                  'osr',    # The description of overlooked security requirement
                  )