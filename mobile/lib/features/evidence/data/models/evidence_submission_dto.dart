// Subset of backend submission responses used by the mobile app.

class JobFormSubmissionDto {
  const JobFormSubmissionDto({
    required this.id,
    required this.jobId,
    required this.formKey,
  });

  final String id;
  final String jobId;
  final String formKey;

  factory JobFormSubmissionDto.fromJson(Map<String, dynamic> json) {
    return JobFormSubmissionDto(
      id: '${json['id']}',
      jobId: '${json['job_id']}',
      formKey: json['form_key'] as String? ?? '',
    );
  }
}
