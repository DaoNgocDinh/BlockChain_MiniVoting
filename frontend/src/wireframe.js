// Presentation examples only: deliberately no signatures, valid certificate or keys.
export const screens = [
  ['network', '01', 'Mạng validator'], ['transaction', '02', 'Giao dịch'],
  ['account', '03', 'Tài khoản'], ['block', '04', 'Block explorer'],
  ['certificate', '05', 'Certificate'], ['timeline', '06', 'Vote timeline'],
]
export const txStates = {
  pending: ['Đang chờ', 'Node đã nhận cục bộ; chưa có block chốt. HTTP 202 chỉ xác nhận accepted.'],
  proposed: ['Đã đề xuất', 'Có trong proposal hợp lệ tại node; chưa cập nhật số dư committed.'],
  committed: ['Đã chốt', 'API tra cứu đọc được giao dịch trong block đã chốt kèm certificate.'],
  rejected: ['Đã loại cục bộ', 'Node còn dấu vết loại với mã lý do; đây là quan sát tại node nguồn.'],
  'local-unknown': ['Node chưa biết', 'Node không giữ thông tin ID này; không suy ra cả mạng đã từ chối.'],
}
export const roundStates = {
  PREPARING: ['PREPARE', 2, 0, 'Đang gom PREPARE. Chưa đủ điều kiện ký COMMIT.'],
  COMMITTING: ['COMMIT', 3, 2, 'Đã prepared. Hai COMMIT chưa đủ quorum 3.'],
  STALLED: ['COMMIT', 3, 2, 'Chờ an toàn. Không hạ quorum, đổi leader hoặc tự mở khóa.'],
  LEADER_UNAVAILABLE: ['PROPOSE', 0, 0, 'Leader cố định không phản hồi. Bản lõi không tự bầu leader.'],
  SYNCING: [null, 0, 0, 'Đang đồng bộ; chỉ đọc snapshot đã chốt gần nhất nếu an toàn.'],
  DECIDED: ['COMMIT', 3, 3, 'Minh họa điều kiện chốt; màn mẫu không kiểm chứng chữ ký.'],
}
export const exampleHash = '0123456789abcdef'.repeat(4)
