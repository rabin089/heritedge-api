# Frontend API Integration Guide (Flutter/Dart)

This guide helps Flutter developers integrate with the HeritEdge backend.

- Base URL: http://localhost:8000
- Auth: Bearer tokens (JWT). Timezone: all timestamps UTC ISO8601.
- Roles: user, reviewer, admin, superadmin.

## Packages

- http (lightweight) or dio (recommended: interceptors, cancel, retries)

```yaml
# pubspec.yaml (either one)
dependencies:
  dio: ^5.5.0
  # http: ^1.2.1
```

## Auth Flow (login + refresh)

- POST `/login` with form fields `username`, `password`.
- Store `access_token` and `refresh_token` securely (e.g., flutter_secure_storage).
- Attach `Authorization: Bearer <access_token>` to subsequent requests.
- On 401 due to expiry, call `POST /refresh-token` with `{ "refresh_token": "..." }` and retry.

### Dio setup with interceptor

```dart
import 'package:dio/dio.dart';

class AuthTokens {
  String? accessToken;
  String? refreshToken;
}

class ApiClient {
  final Dio dio;
  final AuthTokens tokens;

  ApiClient(this.tokens)
      : dio = Dio(BaseOptions(baseUrl: 'http://localhost:8000')) {
    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        if (tokens.accessToken != null) {
          options.headers['Authorization'] = 'Bearer ${tokens.accessToken}';
        }
        return handler.next(options);
      },
      onError: (e, handler) async {
        if (e.response?.statusCode == 401 && tokens.refreshToken != null) {
          try {
            final res = await dio.post('/refresh-token', data: {
              'refresh_token': tokens.refreshToken,
            });
            tokens.accessToken = res.data['access_token'];
            // retry original
            final req = e.requestOptions;
            req.headers['Authorization'] = 'Bearer ${tokens.accessToken}';
            final clone = await dio.fetch(req);
            return handler.resolve(clone);
          } catch (_) {}
        }
        return handler.next(e);
      },
    ));
  }
}
```

## Common Patterns

- Pagination: `page` (>=1), `page_size` (1–100). Responses return `{ items, total, page, page_size }`.
- Filtering/search: `region`, `category`, `tag`, `q` (fuzzy on name/region/description/tags).
- Errors: JSON with `detail` or Pydantic errors. Handle 400/401/403/404/422.

## Contributions

Create a contribution (with images):

```dart
final res = await api.dio.post('/contributions', data: {
  'name': 'Ancient Temple',
  'region': 'Asia',
  'category': 'Cultural',
  'description': 'A historic temple',
  'tags': ['temple', 'heritage'],
  'image_url': 'https://cdn.example.com/images/temple-main.jpg',
  'secondary_images': [
    'https://cdn.example.com/images/temple-1.jpg',
    'https://cdn.example.com/images/temple-2.jpg',
  ],
});
```

Update a pending contribution (partial):

```dart
await api.dio.put('/contributions/123', data: {
  'description': 'Updated',
  'secondary_images': [
    'https://cdn.example.com/images/temple-1.jpg',
    'https://cdn.example.com/images/temple-3.jpg',
  ],
});
```

Resubmit a rejected contribution:

```dart
await api.dio.post('/contributions/123/resubmit', data: {
  'image_url': 'https://cdn.example.com/images/temple-main-v2.jpg',
});
```

My contributions (optional status):

```dart
final res = await api.dio.get('/contributions/me', queryParameters: {
  'status': 'pending', // optional
});
final items = res.data as List;
```

## Notifications (polling)

- List: `GET /notifications`
- Unread count: `GET /notifications/unread-count`
- Mark read: `POST /notifications/read` body `{ ids: [..] }`
- Mark all: `POST /notifications/read-all`

```dart
final list = await api.dio.get('/notifications');
final count = await api.dio.get('/notifications/unread-count');
await api.dio.post('/notifications/read', data: {'ids': [5,6]});
await api.dio.post('/notifications/read-all');
```

Polling suggestion: 30–60s interval, exponential backoff on failure.

## Heritage Sites (public)

```dart
final res = await api.dio.get('/heritage-sites', queryParameters: {
  'q': 'temple',
  'page': 1,
  'page_size': 20,
});
final items = res.data as List; // public array response
```

## Admin Dashboard (admin or reviewer)

Pending contributions with filters + pagination:

```dart
final res = await api.dio.get('/admin/contributions/pending', queryParameters: {
  'region': 'asia',
  'category': 'cultural',
  'q': 'temple',
  'page': 1,
  'page_size': 20,
});
final items = res.data['items'] as List;
final total = res.data['total'];
```

User contribution history:

```dart
final res = await api.dio.get('/admin/user/12/contributions', queryParameters: {
  'status': 'approved', // optional
  'page': 1,
  'page_size': 10,
});
final items = res.data['items'] as List;
```

## Media Handling (images)

- Backend accepts only HTTPS image URLs.
- Optional domain allowlist configured server-side via `IMAGE_ALLOWED_DOMAINS`.
- Current flow: upload media to your storage (S3/GCS/Firebase/CDN), then submit the public HTTPS URLs in payloads.

Tips for Flutter:
- Use `image_picker` to select files, then upload to your storage SDK or via presigned URL (future backend endpoint `/uploads/sign`).
- After upload, pass the final CDN URL into `image_url` or `secondary_images`.

## Error Handling Patterns

```dart
try {
  await api.dio.post('/contributions', data: {/* ... */});
} on DioException catch (e) {
  final status = e.response?.statusCode;
  final data = e.response?.data;
  if (status == 422) {
    // validation error
  } else if (status == 401) {
    // handled via interceptor; if still here, force re-login
  } else if (status == 403) {
    // show permission message
  } else if (status == 404) {
    // not found
  } else {
    // generic error
  }
}
```

## Date/Time

- Timestamps: ISO8601 UTC (e.g., `2025-08-21T12:34:56+00:00`).
- Parse using `DateTime.parse(str).toLocal()` for display.

## Security Notes

- Store tokens securely (e.g., `flutter_secure_storage`).
- Use HTTPS in production for API base URL.
- Consider request timeout: 15–30s, retries for GETs only.

## Checklist for integrating a screen

- Add data fetch with pagination params.
- Wire search field to `q` with debounce (250–400ms).
- Map 401/403/404/422 to user-friendly messages.
- Show `total` and compute total pages.
- For images: validate https URLs on the client, handle fallback placeholders.
